"""Android push UI/bridge behavior with deterministic native and API fakes."""
from pathlib import Path
from playwright.sync_api import expect, sync_playwright

MOCK = '''(() => {
  window.pushFixture={permission:'prompt',nativeConfigured:true,serverConfigured:true,wanted:false,requests:0,settings:0,calls:[],events:{},nativeEvents:{}};
  const f=window.pushFixture;
  window.Capacitor={isNativePlatform:()=>true,Plugins:{
    CipherPush:{getStatus:async()=>({configured:f.nativeConfigured,enabled:f.wanted,notificationsEnabled:f.permission==='granted',installationId:'ec5ca638-3ae2-4e35-ab99-1a2dffdf951e'}),
      setEnabled:async({enabled})=>{f.wanted=enabled;},openSettings:async()=>{f.settings++;},
      addListener:(name,fn)=>{f.nativeEvents[name]=fn;return {remove(){}};},takeLaunchNotification:async()=>({})},
    PushNotifications:{addListener:(name,fn)=>{f.events[name]=fn;return {remove(){}};},
      checkPermissions:async()=>({receive:f.permission}),requestPermissions:async()=>{f.requests++;f.permission=f.deny?'denied':'granted';return {receive:f.permission};},
      createChannel:async(data)=>{f.channel=data;},register:async()=>{if(!f.defer)f.events.registration({value:'fictional_fcm_token_12345678901234567890'});},
      unregister:async()=>{f.unregistered=true;},removeAllDeliveredNotifications:async()=>{} }
  }};
})();'''


def setup(browser, **settings):
    context=browser.new_context(viewport={'width':390,'height':1000})
    context.add_init_script(MOCK)
    page=context.new_page()
    page.goto('http://localhost:8502')
    page.locator('#messages-tab').click()
    page.locator('#chat-password').wait_for()
    page.evaluate('''async(settings)=>{
      Object.assign(window.pushFixture,settings);
      const f=window.pushFixture,m=await import('./messenger-push.js');
      await m.setPushSession({api:async(path,body)=>{f.calls.push({path,body});return path.endsWith('/status')?{configured:f.serverConfigured}:{enabled:true};},onOpen:data=>{f.opened=data;}});
    }''',settings)
    return page


def check():
    output=Path('dist/push-checks');output.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=setup(browser)
        assert page.evaluate('window.pushFixture.requests')==0
        page.locator('#chat-notification-enable').click()
        expect(page.locator('#chat-notification-status')).to_contain_text('Notifications are on')
        assert page.evaluate('window.pushFixture.requests')==1
        assert page.evaluate('window.pushFixture.wanted') is True
        calls=page.evaluate('window.pushFixture.calls')
        registered=[c for c in calls if c['path']=='/api/push/register']
        assert len(registered)==1 and set(registered[0]['body'])=={'token','installationId'}
        assert page.evaluate('window.pushFixture.channel.id')=='ciphercraft_messages'
        page.evaluate("()=>window.pushFixture.events.registration({value:'rotated_fcm_token_12345678901234567890'})")
        page.wait_for_function("window.pushFixture.calls.filter(c=>c.path==='/api/push/register').length===2")
        page.locator('#chat-notification-disable').click()
        expect(page.locator('#chat-notification-status')).to_contain_text('notifications are off')
        assert page.evaluate('window.pushFixture.wanted') is False
        assert page.evaluate('window.pushFixture.unregistered') is True
        denied=setup(browser,deny=True)
        denied.locator('#chat-notification-enable').click()
        expect(denied.locator('#chat-notification-status')).to_contain_text('blocked')
        denied.locator('#chat-notification-settings').click()
        assert denied.evaluate('window.pushFixture.settings')==1
        assert not denied.evaluate("window.pushFixture.calls.some(c=>c.path==='/api/push/register')")
        missing=setup(browser,nativeConfigured=False)
        expect(missing.locator('#chat-notification-enable')).to_be_disabled()
        expect(missing.locator('#chat-notification-status')).to_contain_text('one-time Firebase')
        unavailable=setup(browser,serverConfigured=False)
        unavailable.locator('#chat-notification-enable').click()
        expect(unavailable.locator('#chat-notification-status')).to_contain_text('not configured on the server')
        assert unavailable.evaluate('window.pushFixture.requests')==0
        cancelled=setup(browser,defer=True)
        cancelled.locator('#chat-notification-enable').click()
        cancelled.evaluate("async()=>{const m=await import('./messenger-push.js');m.clearPushSession();}")
        expect(cancelled.locator('#chat-notifications')).to_be_hidden()
        assert not cancelled.evaluate("window.pushFixture.calls.some(c=>c.path==='/api/push/register')")
        page.evaluate("()=>window.pushFixture.nativeEvents.messageNotificationOpened({conversationId:'12',recipientId:'2',messageId:'99'})")
        assert page.evaluate("async()=> (await import('./messenger-push.js')).takePushMessage(1)") is None
        routed=page.evaluate("async()=> (await import('./messenger-push.js')).takePushMessage(2)")
        assert routed=={'conversationId':'12','recipientId':'2','messageId':'99'}
        for width in (320,390,768,1440):
            page.set_viewport_size({'width':width,'height':1000})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
            page.screenshot(path=str(output/f'push-{width}.png'),full_page=True)
        browser.close()
    print('Push component passed: opt-in permission, token registration/rotation, disable, denied/settings, missing setup, signout race, account-scoped tap and four widths.')


if __name__=='__main__':check()

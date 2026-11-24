"""Smooth fixed desktop navigation, mobile chips and reduced-motion behavior."""
import argparse
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def check(url, screenshots):
    output = Path(screenshots)
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={'width': 1440, 'height': 1000})
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)
        track = page.locator('#section-track')
        expect(track.get_by_role('tab')).to_have_count(5)
        expect(page.locator('.tool-tabs')).to_have_count(0)
        expect(page.locator('#nav-previous')).to_have_count(0)
        expect(page.locator('#nav-next')).to_have_count(0)
        # Sample an actual animation halfway through, rather than checking only its end.
        motion = page.evaluate("""()=>{
            const indicator=document.querySelector('#nav-indicator');
            const start=indicator.getBoundingClientRect().left;
            document.querySelector('#learn-tab').click();
            const animation=indicator.getAnimations().at(-1); animation.pause(); animation.currentTime=130;
            const middle=indicator.getBoundingClientRect().left;
            const target=document.querySelector('#learn-tab').getBoundingClientRect().left;
            return {start,middle,target,duration:animation.effect.getTiming().duration};
        }""")
        assert motion['duration'] == 260
        assert motion['start'] < motion['middle'] < motion['target'], motion
        # Interrupting a transition starts at the visible position, without a jump.
        continuity = page.evaluate("""()=>{
            const indicator=document.querySelector('#nav-indicator'); const before=indicator.getBoundingClientRect().left;
            document.querySelector('#hash-tab').click(); const animation=indicator.getAnimations().at(-1);
            animation.pause();animation.currentTime=0;const after=indicator.getBoundingClientRect().left;
            animation.finish();return {before,after};
        }""")
        assert abs(continuity['before'] - continuity['after']) < 1, continuity
        for name in ['manual', 'play', 'hash', 'learn', 'crack']:
            page.locator('#' + name + '-tab').click()
            expect(page.locator('#' + name + '-tab')).to_have_attribute('aria-selected', 'true')
            page.wait_for_function("""()=>{
                const i=document.querySelector('#nav-indicator').getBoundingClientRect();
                const b=document.querySelector('#section-track [aria-selected=true]').getBoundingClientRect();
                return Math.abs(i.left-b.left)<1 && Math.abs(i.width-b.width)<1;
            }""")
        page.locator('#crack-tab').focus()
        page.keyboard.press('End')
        expect(page.locator('#learn-tab')).to_be_focused()
        page.keyboard.press('ArrowRight')
        expect(page.locator('#crack-tab')).to_be_focused()
        page.keyboard.press('ArrowLeft')
        expect(page.locator('#learn-tab')).to_be_focused()
        page.keyboard.press('Home')
        expect(page.locator('#crack-tab')).to_be_focused()
        page.wait_for_timeout(300)
        for width in [768, 1440]:
            page.set_viewport_size({'width': width, 'height': 1000})
            page.wait_for_timeout(300)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert track.evaluate('e=>e.scrollWidth<=e.clientWidth')
            assert track.get_by_role('tab').count() == 5
            page.screenshot(path=str(output / f'desktop-{width}.png'), full_page=True)
        page.emulate_media(reduced_motion='reduce')
        page.locator('#hash-tab').click()
        page.wait_for_function("document.querySelector('#nav-indicator').getAnimations().every(a=>a.effect.getTiming().duration===0)")
        assert page.evaluate("['tools-workspace','play-panel','hash-panel','learn-panel'].every(id=>document.getElementById(id).getAnimations().every(a=>a.playState!=='running'))")
        page.screenshot(path=str(output / 'reduced-motion.png'), full_page=True)
        mobile = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        phone = mobile.new_page()
        phone.goto(url)
        expect(phone.locator('#nav-next')).to_have_count(0)
        expect(phone.locator('#nav-previous')).to_have_count(0)
        rect = phone.locator('#section-track').bounding_box()
        assert phone.locator('#section-track').evaluate('e=>e.scrollWidth>e.clientWidth')
        y = rect['y'] + rect['height'] / 2
        cdp = mobile.new_cdp_session(phone)
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': 345, 'y': y}]})
        for step in range(1, 9):
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': 345 - 270 * step / 8, 'y': y}]})
            phone.wait_for_timeout(20)
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
        phone.wait_for_function('document.querySelector("#section-track").scrollLeft>60')
        # Swiping only scrolls. A deliberate tap selects the section.
        expect(phone.locator('#crack-tab')).to_have_attribute('aria-selected', 'true')
        phone.locator('#learn-tab').tap()
        expect(phone.locator('#learn-content')).to_be_visible()
        for width in [320, 390]:
            phone.set_viewport_size({'width': width, 'height': 844})
            assert phone.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert phone.locator('#learn-tab').bounding_box()['height'] >= 44
            assert phone.locator('#section-track').bounding_box()['height'] < 80
            phone.screenshot(path=str(output / f'chips-{width}.png'), full_page=True)
        assert not errors, errors
        browser.close()
    print('Navigation passed: fixed desktop tabs, measured smooth animation and interrupted continuity, keyboard, native mobile swipe, reduced motion and four viewport widths.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://localhost:8502')
    parser.add_argument('--screenshots', default='dist/nav-checks')
    args = parser.parse_args()
    check(args.url, args.screenshots)

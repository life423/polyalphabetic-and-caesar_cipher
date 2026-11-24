"""Messenger cryptography interoperates, separates auth/backup keys and binds message context."""
import json
import subprocess
from playwright.sync_api import sync_playwright


def node(script, data=None):
    result = subprocess.run(['node', '--input-type=module', '-e', script], input=json.dumps(data).encode() if data else None, capture_output=True, check=True)
    return json.loads(result.stdout)


def check():
    peer = node("import {generateKeyPairSync} from 'node:crypto';const p=generateKeyPairSync('ec',{namedCurve:'prime256v1'});console.log(JSON.stringify({private:p.privateKey.export({format:'jwk'}),public:p.publicKey.export({format:'jwk'})}));")
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(); page.goto('http://localhost:8502')
        result = page.evaluate('''async(peer)=>{
            const m=await import('./messenger-crypto.js');
            const a=await m.createIdentity('fictional-alice-password','alice_crypto');
            const privateKey=await m.unlockIdentity('fictional-alice-password',a.keyBackup,a.publicKey);
            if(privateKey.extractable) throw new Error('Private key must not be exportable');
            const payload={v:1,kind:'challenge',cipher:'Caesar',text:'Khoor zruog! 🔐',hint:'A small shift',hideCipher:false};
            const envelope=await m.encryptChat(privateKey,peer.public,17,3,payload);
            const plain=await m.decryptChat(privateKey,peer.public,17,3,envelope);
            if(JSON.stringify(plain)!==JSON.stringify(payload))throw new Error('Round trip');
            const failures=[];
            for(const [label,fn] of [
              ['wrong backup password',()=>m.unlockIdentity('wrong-fictional-password',a.keyBackup)],
              ['identity substitution',()=>m.unlockIdentity('fictional-alice-password',a.keyBackup,peer.public)],
              ['auth secret cannot unwrap',()=>m.unlockIdentity(a.authSecret,a.keyBackup)],
              ['wrong conversation',()=>m.decryptChat(privateKey,peer.public,18,3,envelope)],
              ['wrong sender',()=>m.decryptChat(privateKey,peer.public,17,4,envelope)],
              ['changed ciphertext',()=>m.decryptChat(privateKey,peer.public,17,3,{...envelope,ct:(envelope.ct[0]==='A'?'B':'A')+envelope.ct.slice(1)})],
              ['invalid version',()=>m.decryptChat(privateKey,peer.public,17,3,{...envelope,v:2})],
              ['invalid payload',()=>m.encryptChat(privateKey,peer.public,17,3,{v:1,kind:'challenge',text:'x',cipher:'unknown'})]
            ]){let failed=false;try{await fn()}catch{failed=true}if(!failed)throw new Error(label);failures.push(label)}
            const repeat=await m.encryptChat(privateKey,peer.public,17,3,payload);
            if(repeat.iv===envelope.iv)throw new Error('Repeated IV');
            if(a.authSecret!==await m.authSecret('fictional-alice-password','ALICE_CRYPTO'))throw new Error('Canonical username');
            return {publicKey:a.publicKey,envelope,payload,failures,fingerprint:await m.fingerprint(a.publicKey)};
        }''', peer)
        assert len(result['failures']) == 8
        script = '''import{createECDH,hkdfSync,createDecipheriv}from'node:crypto';
let text='';for await(const chunk of process.stdin)text+=chunk;
const d=JSON.parse(text),e=createECDH('prime256v1');e.setPrivateKey(Buffer.from(d.peer.private.d,'base64url'));
const p=d.result.publicKey,point=Buffer.concat([Buffer.from([4]),Buffer.from(p.x,'base64url'),Buffer.from(p.y,'base64url')]);
const shared=e.computeSecret(point),key=hkdfSync('sha256',shared,Buffer.from('CipherCraft conversation v1:17'),Buffer.from('authenticated puzzle transport'),32);
const envelope=d.result.envelope,ct=Buffer.from(envelope.ct,'base64url'),cipher=createDecipheriv('aes-256-gcm',key,Buffer.from(envelope.iv,'base64url'));
cipher.setAAD(Buffer.from(JSON.stringify(['CipherCraft chat v1','17','3'])));cipher.setAuthTag(ct.subarray(-16));
console.log(Buffer.concat([cipher.update(ct.subarray(0,-16)),cipher.final()]).toString());'''
        actual = node(script, {'peer': peer, 'result': result})
        assert actual == result['payload']
        b.close()
    print('Messenger crypto passed: independent Node ECDH/HKDF/AES-GCM, password backup, identity binding, auth separation, tamper/context rejection and fresh IVs.')


if __name__ == '__main__':
    check()

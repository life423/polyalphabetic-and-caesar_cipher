"""CipherCraft's browser workspace, served by Streamlit on Azure App Service."""
import streamlit as st

from src.services.cipher_service import CipherService
from src.services.web_service import (
    ANALYZABLE, CIPHERS, MAX_TEXT_LENGTH, analyze_message, candidate_key,
    context_id, decode_upload, describe_key, download_name, transform_message,
)


KEY_FIELDS = {
    'Caesar': 'shift', 'Vigenère': 'keyword', 'Substitution': 'alphabet',
    'Columnar transposition': 'column_key', 'Rail Fence': 'rails',
}


def clear_outputs():
    st.session_state.pop('result', None)
    st.session_state.pop('analysis', None)
    st.session_state.pop('notice', None)


def generate_alphabet():
    st.session_state.alphabet = CipherService().generate_substitution_key()
    st.session_state.pop('result', None)


def use_result():
    result = st.session_state.result
    st.session_state.message = result['text']
    st.session_state.source_mode = 'Text'
    st.session_state.operation = 'Decrypt' if result['operation'] == 'Encrypt' else 'Encrypt'
    clear_outputs()


def apply_candidate():
    analysis = st.session_state.analysis
    cipher = analysis['cipher']
    key = candidate_key(cipher, analysis['candidates'][st.session_state.candidate_choice])
    if cipher == 'Affine':
        st.session_state.affine_a, st.session_state.affine_b = key
    else:
        st.session_state[KEY_FIELDS[cipher]] = key
    st.session_state.operation = 'Decrypt'
    try:
        output = transform_message(analysis['source'], cipher, 'Decrypt', key, analysis['file_mode'])
        st.session_state.result = {
            'text': output, 'cipher': cipher, 'operation': 'Decrypt',
            'context': context_id(analysis['source'], cipher, analysis['file_mode'], 'Decrypt', key),
            'filename': download_name(analysis['filename'], 'Decrypt'),
        }
        st.session_state.active_panel = 'result'
        st.session_state.notice = 'Suggested key applied. Your decrypted result is ready.'
    except ValueError as exc:
        st.session_state.notice = str(exc)


def render_key(cipher):
    if cipher == 'Caesar':
        return st.number_input('Shift', min_value=0, max_value=25, step=1, key='shift',
                               help='0 leaves the message unchanged. A shift of 3 changes A to D.')
    if cipher == 'Vigenère':
        return st.text_input('Keyword', key='keyword', placeholder='For example, LEMON',
                             help='Use letters A–Z. Keep this keyword to decrypt the message later.')
    if cipher == 'Substitution':
        key = st.text_input('Substitution alphabet', key='alphabet', max_chars=26,
                            placeholder='Enter all 26 letters in a new order',
                            help='Each letter A–Z must appear exactly once.')
        st.button('Generate a random key', on_click=generate_alphabet)
        return key
    if cipher == 'Columnar transposition':
        return st.text_input('Keyword or column order', key='column_key', placeholder='ZEBRAS or 2,0,1',
                             help='Numeric columns start at 0 and must each appear once.')
    if cipher == 'Rail Fence':
        return st.number_input('Number of rails', min_value=2, max_value=100, step=1, key='rails',
                               help='Key analysis searches 2–20 rails.')
    first, second = st.columns(2)
    with first:
        a = st.number_input('Multiplier (a)', step=1, key='affine_a',
                            help='Use a value coprime to 26, such as 1, 3, 5, 7, or 11.')
    with second:
        b = st.number_input('Shift (b)', step=1, key='affine_b')
    return a, b


def render_result(current_context):
    result = st.session_state.get('result')
    st.subheader('Result')
    if result is None or result['context'] != current_context:
        st.markdown('Your result will appear here.')
        st.caption('Choose a cipher, enter its key and a message, then encrypt or decrypt.')
        return
    if st.session_state.get('notice'):
        st.success(st.session_state.notice)
    else:
        st.caption(f"{result['operation']}ed with {result['cipher']} · {len(result['text']):,} characters")
    st.code(result['text'], language=None, wrap_lines=True)
    download, reuse = st.columns(2)
    with download:
        st.download_button('Download .txt', data=result['text'].encode('utf-8'),
                           file_name=result['filename'], mime='text/plain; charset=utf-8',
                           use_container_width=True)
    with reuse:
        st.button('Use result as input', on_click=use_result, use_container_width=True)


def render_analysis(analysis_context):
    analysis = st.session_state.get('analysis')
    if analysis is None or analysis['context'] != analysis_context:
        return False
    st.subheader('Key suggestions')
    st.caption('Ranked for English text. Relative scores compare these guesses; they are not probabilities.')
    if analysis['file_mode'] and analysis['cipher'] in ('Vigenère', 'Rail Fence'):
        st.caption('Analyzed the longest letter-bearing line because file ciphers restart each line.')
    candidates = analysis['candidates']
    if not candidates:
        st.info('No usable key suggestions. Try a longer English ciphertext sample.')
        return True
    index = st.radio(
        'Choose a suggested key', options=range(len(candidates)), key='candidate_choice',
        format_func=lambda i: (
            f"{describe_key(analysis['cipher'], candidate_key(analysis['cipher'], candidates[i]))}"
            f" · relative score {candidates[i]['confidence']}%"
        ),
    )
    st.caption('Plaintext preview')
    st.code(candidates[index]['sample'], language=None, wrap_lines=True)
    st.button('Use key & decrypt', type='primary', on_click=apply_candidate, use_container_width=True)
    return True


def main():
    st.set_page_config(page_title='CipherCraft — Classical ciphers', page_icon='🔐', layout='wide')
    defaults = {
        'cipher': 'Caesar', 'operation': 'Encrypt', 'source_mode': 'Text', 'message': '',
        'shift': 3, 'keyword': '', 'alphabet': '', 'column_key': '', 'rails': 3,
        'affine_a': 5, 'affine_b': 8, 'active_panel': 'result', 'candidate_choice': 0,
    }
    for name, value in defaults.items():
        if name not in st.session_state:
            st.session_state[name] = value

    st.html('''<style>
        .block-container {max-width:1180px;padding-top:1.5rem;padding-bottom:2rem;}
        .brand {background:#2D3E50;color:white;padding:24px 28px;border-radius:10px;margin-bottom:24px;}
        .brand h1 {font-size:2rem;font-weight:700;letter-spacing:-.04em;color:white;margin:0;padding:0;}
        .brand p {color:#D7E5EE;font-size:1rem;line-height:1.5;margin:6px 0 0;}
        .st-key-settings, .st-key-editor, .st-key-result {background:#FFFFFF;}
        [data-testid="stCode"] pre {white-space:pre-wrap;word-break:break-word;}
        [data-testid="stCaptionContainer"] {opacity:1;}
        [data-testid="stCaptionContainer"] p {color:#526478;}
        [data-testid="stButton"] button, [data-testid="stDownloadButton"] button,
        .st-key-operation button {min-height:44px;}
        [data-testid="stRadio"] label {min-height:44px;align-items:center;}
        textarea::placeholder, input::placeholder {color:#64748B;opacity:1;}
        button, a, input, textarea {scroll-margin:16px;}
        @media (max-width:640px) {
            .block-container {padding:1rem;}
            .brand {padding:20px;margin-bottom:16px;}
            .brand h1 {font-size:1.75rem;}
            [data-testid="stHorizontalBlock"] {flex-wrap:wrap;}
            [data-testid="stColumn"] {min-width:min(100%,260px);flex:1 1 260px;}
        }
        @media (prefers-reduced-motion:reduce) {*,*::before,*::after {scroll-behavior:auto!important;}}
    </style>
    <header class="brand"><h1>CipherCraft</h1><p>Encrypt, decrypt, and explore classical ciphers.</p></header>''')

    with st.container(border=True, key='settings'):
        cipher_column, operation_column = st.columns([1.5, 1])
        with cipher_column:
            cipher = st.selectbox('Cipher', list(CIPHERS), key='cipher', on_change=clear_outputs)
        with operation_column:
            operation = st.segmented_control('Operation', ['Encrypt', 'Decrypt'], key='operation',
                                             selection_mode='single', required=True)
        key = render_key(cipher)
        if cipher in ('Columnar transposition', 'Rail Fence'):
            st.caption('Encryption removes spaces within each message. Columnar transposition also adds X padding.')

    editor, output = st.columns([1, 1], gap='large')
    text, filename, input_error = '', 'message.txt', None
    with editor:
        with st.container(border=True, key='editor'):
            st.subheader('Message')
            mode = st.radio('Input source', ['Text', 'Text file'], horizontal=True, key='source_mode',
                            on_change=clear_outputs)
            file_mode = mode == 'Text file'
            if file_mode:
                uploaded = st.file_uploader('Choose a UTF-8 .txt file', type=['txt'], key='upload')
                if uploaded is not None:
                    filename = uploaded.name
                    try:
                        text = decode_upload(uploaded.getvalue())
                        st.text_area('File preview', value=text[:2000], height=180, disabled=True)
                        st.caption(f'{len(text):,} characters · original file stays on your device.')
                    except ValueError as exc:
                        input_error = str(exc)
                        st.error(input_error)
                st.caption('Up to 1 MB and 100,000 characters. File lines are processed independently.')
            else:
                text = st.text_area('Your message', key='message', height=220,
                                    placeholder='Type or paste a message…', max_chars=MAX_TEXT_LENGTH)
                st.caption(f'{len(text):,} / 100,000 characters')

            process = st.button(f'{operation} message', type='primary', use_container_width=True,
                                disabled=bool(input_error))
            analyze = st.button('Analyze ciphertext', use_container_width=True,
                                disabled=cipher not in ANALYZABLE or bool(input_error),
                                help='Suggest keys from up to 5,000 characters of English ciphertext. No key is needed.')
            if cipher not in ANALYZABLE:
                st.caption('Key analysis is available for Caesar, Vigenère, Rail Fence, and Affine.')

            if process:
                try:
                    with st.spinner(f'{operation}ing message…'):
                        result = transform_message(text, cipher, operation, key, file_mode)
                    st.session_state.result = {
                        'text': result, 'cipher': cipher, 'operation': operation,
                        'context': context_id(text, cipher, file_mode, operation, key),
                        'filename': download_name(filename, operation),
                    }
                    st.session_state.active_panel = 'result'
                    st.session_state.pop('notice', None)
                except ValueError as exc:
                    st.session_state.pop('result', None)
                    st.error(str(exc))
            if analyze:
                try:
                    with st.spinner('Comparing possible keys…'):
                        candidates = analyze_message(text, cipher, file_mode)
                    st.session_state.analysis = {
                        'source': text, 'cipher': cipher, 'file_mode': file_mode, 'filename': filename,
                        'candidates': candidates, 'context': context_id(text, cipher, file_mode),
                    }
                    st.session_state.candidate_choice = 0
                    st.session_state.active_panel = 'analysis'
                except ValueError as exc:
                    st.session_state.pop('analysis', None)
                    st.error(str(exc))

    with output:
        with st.container(border=True, key='result'):
            showing_analysis = False
            if st.session_state.active_panel == 'analysis':
                showing_analysis = render_analysis(context_id(text, cipher, file_mode))
            if not showing_analysis:
                render_result(context_id(text, cipher, file_mode, operation, key))

    st.caption('Educational tool · Classical ciphers are not secure encryption. '
               'Uploads are processed in memory; CipherCraft does not save your messages or files.')


if __name__ == '__main__':
    main()

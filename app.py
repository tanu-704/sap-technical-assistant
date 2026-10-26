"""Run with: python -m streamlit run app.py"""
from io import BytesIO
import hmac
import json
import os
import streamlit as st
from assistant_core import SYSTEM_PROMPT,build_messages,clip_text,transcript_markdown
from fix_tools import inspect_fix,frame_fix

st.set_page_config(page_title='SAP Technical Assistant',page_icon='🧩',layout='wide')
st.markdown('''<style>
.block-container {max-width:1200px;padding-top:2.1rem}
[data-testid="stSidebar"] {border-right:1px solid #2B3D55}
.hero {padding:1.8rem;border:1px solid #304764;border-radius:22px;background:linear-gradient(125deg,#132D3B,#1B2441);margin-bottom:1.4rem}
.eyebrow {font-size:.8rem;letter-spacing:.15em;color:#83E7D3;font-weight:700}
.hero h1 {margin:.3rem 0;color:#EDF3FC;font-size:2.35rem}
.hero p {color:#B9C9DD;margin-bottom:0}
</style>''',unsafe_allow_html=True)

def setting(name,default=''):
    try:return str(st.secrets.get(name,os.environ.get(name,default)))
    except FileNotFoundError:return os.environ.get(name,default)

server_key=setting('OPENAI_API_KEY')
app_password=setting('APP_PASSWORD')
model=setting('OPENAI_MODEL','gpt-5.4-mini')
for key,value in [('messages',[]),('pending_prompt',''),('upload_epoch',0),('requests_sent',0)]:
    if key not in st.session_state:st.session_state[key]=value

with st.sidebar:
    st.markdown('### 🧩 SAP Technical Assistant')
    st.caption('Your troubleshooting workspace')
    area=st.selectbox('SAP area',['General SAP','ACM and commodity trading','Trade finance and pricing','ABAP development','Integration and FIX','Basis and authorizations','MM and procurement','SD and sales','FI and accounting'])
    environment=st.selectbox('Environment',['Not specified','DEV','UAT / Quality','Production'])
    release=st.text_input('SAP release or application',placeholder='For example: S/4HANA, ECC, custom app',max_chars=150)
    language=st.selectbox('Response language',['English','Hindi','Hinglish'])
    detail=st.selectbox('Answer style',['Practical and concise','Detailed steps','Beginner friendly'])
    with st.expander('AI connection',expanded=not bool(server_key)):
        mode=st.radio('API key source',['Use app owner key','Use my own key']) if server_key else 'Use my own key'
        if mode=='Use app owner key':
            if not app_password or app_password.startswith('REPLACE_'):
                st.warning('The app owner must configure a private APP_PASSWORD before the shared API key can be used.')
                api_key=''
            else:
                password=st.text_input('App password',type='password',key='owner_password')
                unlocked=bool(password) and hmac.compare_digest(password.encode(),app_password.encode())
                api_key=server_key if unlocked else ''
                if password and not unlocked:st.caption('Password does not match.')
                elif unlocked:st.success('AI chat unlocked')
        else:
            api_key=st.text_input('Your OpenAI API key',type='password',key='visitor_api_key',placeholder='sk-...').strip()
            st.caption('Used for this browser session. Your API account is charged for requests.')
        st.caption('API use is billed separately from a ChatGPT subscription. The local FIX tool works without a key.')
    st.divider()
    a,b=st.columns(2)
    with a:
        if st.button('New chat',use_container_width=True):
            st.session_state.messages=[];st.session_state.pending_prompt='';st.rerun()
    with b:
        if st.button('Clear files',use_container_width=True):
            st.session_state.upload_epoch+=1;st.rerun()
    if st.session_state.messages:
        st.download_button('Download conversation',transcript_markdown(st.session_state.messages),file_name='sap_conversation.md',mime='text/markdown',use_container_width=True)
    st.caption('No SAP connection or live SAP documentation search. Verify release-specific advice in your system.')

st.markdown('''<div class="hero"><div class="eyebrow">DIAGNOSE · UNDERSTAND · RESOLVE</div>
<h1>SAP Technical Assistant</h1><p>Bring the error. Trace the cause. Build the next step.</p></div>''',unsafe_allow_html=True)
chat_tab,issue_tab,fix_tab=st.tabs(['💬 Ask the assistant','📋 Structure an issue','🔎 FIX message tools'])

with chat_tab:
    with st.expander('Attach logs or reference material',expanded=False):
        uploads=st.file_uploader('Upload up to 3 files: text, logs, ABAP, CSV, JSON or text-based PDF',type=['txt','log','md','csv','json','abap','pdf'],accept_multiple_files=True,key=f'uploads_{st.session_state.upload_epoch}')
        st.caption('Messages and included file text are sent to OpenAI when you press Send. Remove credentials and use only material you are authorized to share. Files are processed in memory.')
    references=[]
    if uploads:
        if len(uploads)>3:st.warning('Only the first 3 files are included.')
        for file in uploads[:3]:
            try:
                if file.size>5*1024*1024:raise ValueError('File is larger than 5 MB')
                raw=file.getvalue()
                if file.name.lower().endswith('.pdf'):
                    from pypdf import PdfReader
                    reader=PdfReader(BytesIO(raw))
                    if reader.is_encrypted:raise ValueError('Use an unencrypted PDF')
                    parts=[];char_count=0;has_text=False
                    for i,page in enumerate(reader.pages[:30],1):
                        extracted=page.extract_text() or ''
                        has_text=has_text or bool(extracted.strip())
                        parts.append(f'Page {i}\n'+extracted);char_count+=len(extracted)
                        if char_count>14000:break
                    text='\n\n'.join(parts)
                    if not has_text:raise ValueError('No readable text. Scanned images need OCR before upload.')
                    if not any((p.extract_text() or '').strip() for p in reader.pages[:1]):
                        st.caption(file.name+': the first page has little or no extractable text.')
                else:
                    try:text=raw.decode('utf-8-sig')
                    except UnicodeDecodeError:raise ValueError('Save this text file with UTF-8 encoding') from None
                if not text.strip():raise ValueError('File has no text')
                references.append((file.name,clip_text(text,14000)))
                st.caption(f'Attached: {file.name} · {min(len(text),14000):,} characters extracted; a bounded excerpt is included in requests.')
            except Exception as exc:
                st.warning(file.name+': '+str(exc)[:200])
    if not st.session_state.messages:
        st.subheader('What are you working on?')
        starters=[
            ('🔧 Diagnose an SAP error','Help me diagnose an SAP error. Ask for the transaction, exact error, reproduction steps, system release and relevant logs before confirming a root cause.'),
            ('🧑‍💻 Explain ABAP or a dump','Help me analyze ABAP code or a short dump. Tell me which code excerpt, ST22 details and runtime context you need.'),
            ('🌾 ACM and pricing','Help me troubleshoot a commodity contract or pricing issue in SAP ACM. Start by asking about the document, lifecycle step and observed behavior.'),
            ('📝 Draft an OSS case','Help me draft an SAP support case from the facts I provide. Do not invent impact, evidence, document numbers or reproduction results.')]
        cols=st.columns(2)
        for i,(label,prompt) in enumerate(starters):
            with cols[i%2]:
                if st.button(label,use_container_width=True):st.session_state.pending_prompt=prompt
    for message in st.session_state.messages:
        with st.chat_message(message['role']):st.markdown(message['content'])
    question=st.chat_input('Describe the SAP issue, paste the exact error, or ask a technical question',max_chars=6000)
    pending=st.session_state.pending_prompt
    if pending:
        st.info(pending)
        left,right=st.columns([1,1])
        with left:
            if st.button('Send prepared question',type='primary'):
                question=pending;st.session_state.pending_prompt=''
        with right:
            if st.button('Discard prepared question'):
                st.session_state.pending_prompt='';st.rerun()
    if question:
        if not api_key:
            st.info('Set up the AI connection in the sidebar before sending. You can use Structure an issue and FIX message tools without a key.')
            st.session_state.pending_prompt=question
        else:
            history=st.session_state.messages[:]
            st.session_state.messages.append({'role':'user','content':question})
            with st.chat_message('user'):st.markdown(question)
            meta=json.dumps({'SAP area':area,'environment':environment,'release or application':release},ensure_ascii=False)
            evidence=[('System context supplied by user',meta)]+references
            messages=build_messages(history,question,evidence)
            instructions=SYSTEM_PROMPT+f'\nResponse language: {language}. Answer style: {detail}.'
            with st.chat_message('assistant'):
                try:
                    from openai import OpenAI,AuthenticationError,RateLimitError,APIConnectionError,APIStatusError
                    def stream_answer():
                        with OpenAI(api_key=api_key,timeout=90,max_retries=1) as client:
                            with client.responses.create(model=model,instructions=instructions,input=messages,
                                max_output_tokens=3500,reasoning={'effort':'low'},stream=True,store=False) as stream:
                                complete=False
                                for event in stream:
                                    if event.type=='response.output_text.delta':yield event.delta
                                    elif event.type in ('response.failed','error'):
                                        raise RuntimeError('The AI request failed. Check model access, account status and the server logs.')
                                    elif event.type=='response.incomplete':
                                        raise RuntimeError('The answer was cut short. Ask a narrower question or increase max_output_tokens in app.py.')
                                    elif event.type=='response.completed':complete=True
                                if not complete:raise RuntimeError('The response did not complete. Please try again.')
                    with st.spinner('Working through your SAP question...'):
                        answer=st.write_stream(stream_answer())
                    if not isinstance(answer,str) or not answer.strip():raise RuntimeError('No text answer returned. Please try a narrower question.')
                    st.session_state.messages.append({'role':'assistant','content':answer})
                    st.session_state.requests_sent+=1
                except Exception as exc:
                    # Do not display raw provider errors or credentials.
                    name=type(exc).__name__
                    if name=='AuthenticationError':note='The API key was not accepted. Check it in the sidebar or Streamlit Secrets.'
                    elif name=='RateLimitError':note='The API account has reached a rate or quota limit. Check API billing and limits, then retry.'
                    elif name in ('APIConnectionError','APITimeoutError'):note='The AI service could not be reached in time. Please retry.'
                    elif name=='APIStatusError':note='The AI service rejected this request. Check the configured model and account access.'
                    elif isinstance(exc,RuntimeError):note=str(exc)
                    else:note='The request could not complete. Confirm that requirements.txt was installed and the AI connection is configured.'
                    st.error(note)
                    st.caption('An incomplete answer is not saved as a completed reply. Your question remains in the conversation.')

with issue_tab:
    st.subheader('Turn a rough issue into a useful troubleshooting brief')
    transaction=st.text_input('Transaction, application or interface',placeholder='For example: custom pricing app, SWC, FIX interface',max_chars=200)
    exact_error=st.text_area('Exact error or unexpected behavior',height=110,max_chars=2500)
    expected=st.text_area('Expected behavior',max_chars=1000)
    steps=st.text_area('Steps to reproduce',placeholder='1. ...\n2. ...',max_chars=2000)
    evidence=st.text_area('What you already checked',max_chars=1500)
    template=f'''Please help diagnose this SAP issue. Separate evidence from possible causes and give checks to distinguish them.
SAP area: {area}
Environment: {environment}
Release/application: {release or 'Not provided'}
Transaction/interface: {transaction or 'Not provided'}
Observed behavior/error: {exact_error or 'Not provided'}
Expected behavior: {expected or 'Not provided'}
Steps to reproduce: {steps or 'Not provided'}
Checks already performed: {evidence or 'Not provided'}
Do not assume an unprovided document state or root cause.'''
    st.download_button('Download issue brief',template,file_name='sap_issue_brief.txt',mime='text/plain')
    if st.button('Prepare this issue for chat',type='primary'):
        st.session_state.pending_prompt=clip_text(template,6000)
        st.success('Prepared. Open Ask the assistant and click Send prepared question.')

with fix_tab:
    st.subheader('Calculate the framing. Keep your order details intact.')
    st.caption('Local ASCII FIX checks; no API key required. Pipes represent SOH bytes. This tool does not submit messages, validate broker rules or confirm order states.')
    fix_mode=st.radio('Action',['Validate complete message','Add BodyLength and CheckSum'],horizontal=True)
    version=st.selectbox('FIX version',['FIX.4.4','FIX.4.2']) if fix_mode=='Add BodyLength and CheckSum' else 'FIX.4.4'
    fix_input=st.text_area('Paste one message or body',height=160,placeholder='8=FIX.4.4|9=...|35=...|...|10=...|',max_chars=40000)
    if fix_mode=='Add BodyLength and CheckSum':
        st.info('Paste the body starting with 35= and ending with |. Remove tags 8, 9 and 10. The tool adds only framing fields.')
    if st.button('Run FIX check',type='primary'):
        try:
            message=frame_fix(fix_input,version) if fix_mode=='Add BodyLength and CheckSum' else fix_input
            result=inspect_fix(message)
            a,b,c=st.columns(3)
            a.metric('Calculated BodyLength',result['calculated_body_length'])
            b.metric('Calculated CheckSum',f"{result['calculated_checksum']:03d}")
            c.metric('Message type',result['message_type'])
            if result['valid']:st.success('BodyLength and CheckSum match the message bytes.')
            else:st.error('Framing mismatch. Compare the declared and calculated fields below.')
            st.write({'declared_body_length':result['declared_body_length'],'declared_checksum':result['declared_checksum']})
            if result['duplicate_tags']:st.warning('Repeated tags: '+', '.join(result['duplicate_tags'])+'. These may be valid repeating-group members; check the FIX dictionary and group structure.')
            st.code(message,language='text')
            st.dataframe([{'Tag':tag,'Value':value} for tag,value in result['fields']],hide_index=True,use_container_width=True)
        except ValueError as exc:st.warning(str(exc))

st.caption('SAP Technical Assistant · AI guidance plus local diagnostic tools · Conversations last for this browser session unless you download them.')

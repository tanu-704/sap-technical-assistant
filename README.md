# SAP Technical Assistant

A Streamlit chatbot and diagnostic workspace for SAP technical questions, ABAP, ACM and commodity trading, pricing and trade finance, integration, Basis, MM, SD and FI. It combines AI chat with a structured troubleshooting brief and a local FIX framing tool.

## What is included

- A dark interface with SAP-area, environment, release, language and answer-style controls.
- English, Hindi and Hinglish answers.
- Streaming technical chat and code explanations.
- Text-based PDF, log, TXT, Markdown, CSV, JSON and ABAP file attachments.
- A guided issue brief for root-cause investigation or SAP support-case preparation.
- Chat download as Markdown and issue-brief download as text.
- A deterministic FIX tool for calculating and checking tags 9 and 10.
- Session-scoped chat history, reference excerpts and credentials.
- An app-password gate when using the app owner's API key, or visitor-supplied API keys.

The AI chat requires a working OpenAI API key and API billing/credits. A ChatGPT subscription is not an API key and does not supply this app with API credits. The issue-brief builder and local FIX tools work without an API key. No API key or actual password is included in this download.

There is no connection to SAP, Jira, GitHub or the internet in the chatbot. It cannot read live SAP data or SAP Notes, change configurations, submit FIX orders or confirm transactions. It uses model knowledge, your messages and attached text. It is an assistant, not an authoritative SAP support service.

## 1 Extract the package

Download SAP_Technical_Assistant_Starter.zip and use Extract All on Windows. Open the sap-technical-assistant folder. You should see app.py, assistant_core.py, fix_tools.py and requirements.txt together.

No Python installation is needed on your laptop for the GitHub website / Streamlit Cloud deployment route.

## 2 Create a GitHub repository

1. Open https://github.com/new while signed in to your GitHub account.
2. Name the repository sap-technical-assistant.
3. Select Public for this straightforward upload flow and create it. Add a README if you need an initial commit before uploading.
4. Choose Add file -> Upload files.
5. Upload the CONTENTS of the extracted folder. Do not upload just the ZIP, and do not put another sap-technical-assistant folder around app.py inside the repository.
6. Commit to main. Confirm that app.py, assistant_core.py, fix_tools.py and requirements.txt are visible on the repository's first page.
7. Upload README.md, secrets.example.toml, the tests folder and .gitignore too. The examples contain placeholders only.
8. If the hidden .streamlit folder did not upload, use Add file -> Create new file. Set the filename to .streamlit/config.toml, paste the supplied config.toml contents and commit. This supplies the theme and file-upload limit.

Do not commit a real API key, a real app password, .env or .streamlit/secrets.toml to GitHub. Use Streamlit Secrets instead. The supplied .gitignore excludes those local secret files when using Git.

## 3 Obtain an API key

1. Open https://platform.openai.com/ and sign in to the account you want to pay for this app's AI requests.
2. Set up API billing/credits and check the API limits for that project. ChatGPT plan billing is separate.
3. Open the API keys page at https://platform.openai.com/api-keys and create a project API key. Grant the permissions needed to create Responses API requests, or use a standard project key while setting up your personal app.
4. Copy the key privately. Do not paste it into this chat or GitHub.
5. The default model is gpt-5.4-mini. Your project must be able to use it. OPENAI_MODEL can be changed by the app owner to another Responses-compatible model supporting reasoning effort low. Arbitrary models are not guaranteed compatible with this request configuration.

If you already have a working API key with access to this model, reuse it rather than creating another unnecessarily.

## 4 Deploy on Streamlit

1. Open https://share.streamlit.io/ and sign in using GitHub.
2. Authorize the GitHub connection if prompted and select your account's workspace.
3. Click Create app and choose the option for an existing app.
4. Fill in:

| Setting | Value |
| --- | --- |
| Repository | tanu-704/sap-technical-assistant |
| Branch | main |
| Main file path | app.py |
| Suggested subdomain | tanu-sap-assistant, if available |
| Python version under Advanced settings | 3.11 |

5. In Advanced settings -> Secrets, add the following with your REAL values privately:

```toml
OPENAI_API_KEY = "your-real-api-key"
APP_PASSWORD = "a-long-private-password-you-choose"
OPENAI_MODEL = "gpt-5.4-mini"
```

6. Click Deploy and wait for dependencies to install. You can also add or update secrets later through the app's settings.
7. Open the actual URL Streamlit provides. https://tanu-sap-assistant.streamlit.app/ is only a proposed address until deployment succeeds; it is not a pre-created link.
8. In the sidebar open AI connection, select Use app owner key and enter your APP_PASSWORD. This is a password for this chatbot, not your SAP password.
9. Ask a simple SAP question to verify a streamed answer. Then try an error log and the FIX tool.

This creates a separate chatbot deployment; it does not replace your music app.

### Alternative Use your own key in the sidebar

You may deploy with no secrets at all. The interface and local tools still open. Enter a working API key under AI connection to use AI chat for that browser session. Each visitor must provide their own key in this configuration. The typed key is processed by your Streamlit server; only enter it into a deployment whose owner you trust.

If OPENAI_API_KEY is configured but APP_PASSWORD is missing, the app intentionally disables use of the owner key. Visitor-owned keys and the local tools still work.

## 5 Use the chatbot

### Ask the assistant

1. Select SAP area, environment and release in the sidebar.
2. Optionally select Hindi or Hinglish and an answer style.
3. Open Attach logs or reference material and upload up to three files, each no larger than 5 MB. Plain text must be UTF-8. PDFs must contain selectable text; scanned PDFs/screenshots need OCR first.
4. Enter a question, or select a starter and then click Send prepared question. No AI request is made until you send.
5. The assistant streams the answer. Ask follow-up questions in the same session.
6. Use Download conversation to keep a Markdown copy.

File excerpts are line-numbered. The assistant is instructed to cite existing file lines and distinguish evidence from hypotheses, but citations and advice can still be wrong. It does not browse official SAP documentation. Always check release-specific details.

Only bounded excerpts are sent: up to 12 recent messages (each shortened if needed), about 36,000 history characters total, 18,000 reference characters total and 6,000 question characters. These are character limits, not token guarantees. File references are included afresh on each request while the files remain attached. Long files may be truncated, and older chat content may drop out of context.

### Structure an issue

Enter the transaction/application, exact error, expected behavior, reproduction steps and checks already performed. Download the issue brief or click Prepare this issue for chat, switch to Ask the assistant and click Send prepared question. This is useful for asking a focused diagnostic question without forgetting important context.

### FIX message tools

Use Validate complete message for a single ASCII FIX message with tags 8, 9 and 10, including the final separator. Pipe characters represent actual SOH bytes when calculating framing.

Use Add BodyLength and CheckSum to paste a message BODY starting with 35= and ending with a separator. Remove tags 8, 9 and 10; select FIX.4.4 or FIX.4.2. The tool adds the framing fields with calculated values.

The tool calculates BodyLength and CheckSum and lists repeated tags. A repeated tag is not automatically an error because repeating groups may use it. The tool does not fully validate FIX dictionaries, required business fields, group membership, sequence numbers, ClOrdID chains, broker routing, fill quantities or SAP status transitions. A framing-valid message can still be rejected by your application. Output uses pipes for readability; an actual FIX engine must use SOH bytes if its input interface requires them.

## Example questions

- Here is an ST22 dump and the relevant ABAP. Identify the failing statement, explain the evidence and give read-only checks before suggesting a change.
- Help investigate a commodity pricing issue in SAP ACM. Ask me for the contract state, pricing step and relevant application messages before confirming the cause.
- Create a UAT test template for a 42,000 MT contract with six lots. Leave any expected business results that depend on configuration for me to confirm.
- Turn these verified facts into an SAP support case draft, including expected vs actual behavior and reproduction steps.
- Explain the difference between OrderID, ClOrdID and OrigClOrdID, then help inspect my supplied FIX chain without inventing broker identifiers.

## Data handling and sharing

Chat messages and selected reference text are transmitted from the Streamlit server to OpenAI on each sent request. Requests set store=False, which controls Responses API storage; it does not promise zero retention or override the provider's account-specific logging/data policies. The application does not upload source files to an OpenAI Files API or deliberately save chats/files to disk. Streamlit session memory is temporary. Download conversations or briefs before leaving if you want to keep them.

New chat clears the visible conversation but retains attached files and the current AI connection; Clear files removes the uploader selection. A page refresh, server restart or session expiry may discard session data. Avoid credentials and data you are not authorized to share.

The owner-key password is a shared gate for a small personal/team app, not enterprise identity, per-user permissions or audit logging. Sharing the password allows recipients to use the owner's API balance. API requests have bounded output and retries, but this app does not enforce a global spending cap, rate limit or durable quota. Review usage in the provider dashboard and rotate exposed keys. Larger deployments need stronger access control.

## Run locally on Windows

Install Python 3.11, open a terminal in the extracted folder and run:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py
```

Enter your API key in the sidebar. Alternatively create .streamlit/secrets.toml locally using secrets.example.toml as a template, fill in the values privately and keep the file out of Git.

To run the core tests:

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

## Troubleshooting

| Symptom | Check |
| --- | --- |
| AI chat asks for a key | Enter a key in the sidebar or configure OPENAI_API_KEY and APP_PASSWORD in Streamlit Secrets. |
| Owner key disabled | APP_PASSWORD must be set to a real non-placeholder value. |
| Authentication error | Confirm that the key is valid, has Responses permissions and belongs to the intended API project. |
| Rate or quota limit | Check API billing/credits, model access and usage limits. A ChatGPT subscription does not resolve API quota errors. |
| Model request rejected | Verify model access and OPENAI_MODEL. Use the supplied default to start. |
| Generic error page | Open Streamlit Manage app logs and inspect the full traceback. |
| Import error | Check that all three Python files and requirements.txt are at the repository root and Python 3.11 is selected. |
| PDF has no readable text | Use a text-based PDF or OCR it first; image-only screenshots are not read by this app. |
| Answer is cut short | Ask a narrower question. The configured output budget includes reasoning tokens. |
| Old UI after editing | Commit to the connected branch and refresh or reboot the Streamlit app. |

## Files

| File | Purpose |
| --- | --- |
| app.py | Streamlit interface, AI calls, attachment extraction and tools |
| assistant_core.py | SAP instructions, bounded chat context and exports |
| fix_tools.py | Local FIX framing calculations |
| requirements.txt | Pinned Python dependencies |
| secrets.example.toml | Placeholder configuration to copy privately into Streamlit Secrets |
| .streamlit/config.toml | Theme and upload limit |
| tests/test_core.py | Ten deterministic tests |

## Validation and limits

Ten deterministic tests pass for context handling, history bounds, source line numbering, Unicode truncation, chat exports, FIX SOH-byte calculations, tamper detection, duplicate-tag preservation and invalid input. All Python files were syntax-compiled and the ZIP was checked for corruption.

The authoring environment does not have this app's dependency stack or API credentials and blocks external dependency downloads. The full Streamlit UI, SDK call, PDF uploads, password interactions and live API responses have not been integration-tested here. Your first deployment and test question are the required integration check. No live SAP connection or real transaction testing was performed.

## Technical references

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- https://developers.openai.com/api/docs/quickstart
- https://developers.openai.com/api/docs/models/gpt-5.4-mini
- https://developers.openai.com/api/docs/guides/streaming-responses
- https://developers.openai.com/api/docs/guides/your-data

This is an independent assistant and is not an official SAP product or SAP support channel.

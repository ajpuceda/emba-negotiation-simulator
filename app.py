import streamlit as st
try:
    from mistralai import Mistral
except ImportError:
    try:
        from mistralai.client import Mistral
    except ImportError:
        # Compatibilidad con versiones heredadas muy antiguas
        from mistralai.client import MistralClient as Mistral
import json
import re
import os
import time
import pandas as pd

# ========================================================================
# 🏢 GENERAL CORPORATE INTERFACE CONFIGURATION
# ========================================================================
st.set_page_config(
    page_title="AI Negotiation Soft Skills Coach", 
    page_icon="🤝", 
    layout="wide"
)

# Secure initialization of the native Mistral client using Streamlit secrets
@st.cache_resource
def get_mistral_client():
    api_key = st.secrets.get("MISTRAL_API_KEY", os.environ.get("MISTRAL_API_KEY", ""))
    if not api_key:
        st.error("Missing MISTRAL_API_KEY in secrets or environment variables.")
    return Mistral(api_key=api_key)

client = get_mistral_client()

# Constante global para el modelo menos avanzado de Mistral AI
MISTRAL_MODEL = "mistral-small-latest"

# ========================================================================
# 🛡️ FUNCIÓN DE LLAMADA SEGURA CON AUTO-RECUPERACIÓN (ANTI-429)
# ========================================================================
def safe_mistral_call(messages_payload, temperature=0.7, max_retries=5):
    """
    Ejecuta llamadas al API de Mistral manteniendo la calidad intacta al 100%.
    Si golpea el Rate Limit (429), pausa la ejecución y reintenta automáticamente.
    """
    for attempt in range(max_retries):
        try:
            response = client.chat.complete(
                model=MISTRAL_MODEL,
                messages=messages_payload,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "rate_limited" in error_msg.lower():
                wait_time = 3 * (attempt + 1)
                st.warning(f"⚠️ Mistral Rate Limit hit. Breathing for {wait_time} seconds to protect prompt quality... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise e
    raise Exception("Could not complete the API request due to severe rate limits. Please try again.")
# ========================================================================
# 🧮 FINANCIAL METADATA EXTRACTION INFRASTRUCTURE
# ========================================================================
def extract_financial_data(text):
    """
    Surgically extracts the hidden JSON flow (DATA_STREAM) injected
    by the AI counterpart to update the control backend.
    """
    if not text:
        return None
    match = re.search(r"DATA_STREAM:\s*(\{.*?\})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    return None
def render_justified_report(report_text):
    """
    Parses raw markdown headers and wraps paragraphs in justified HTML blocks.
    Surgically purges ALL types of unicode/orphan bullets and hides decoration artifacts.
    """
    if not report_text:
        return
        
    raw_lines = report_text.split("\n")
    cleaned_lines = []
    
    for line in raw_lines:
        strip_line = line.strip()
        if not strip_line or re.match(r"^[\s\-_*•▪▫◦¶.·]*$", strip_line):
            continue
        cleaned_lines.append(strip_line)

    compiled_html = ""
    current_paragraph_lines = []
    
    def flush_paragraph():
        if current_paragraph_lines:
            paragraph_content = " ".join(current_paragraph_lines).strip()
            if paragraph_content:
                return f'<p style="text-align: justify; text-justify: inter-word; font-size: 15px; color: #212529; line-height: 1.6; margin-bottom: 16px;">{paragraph_content}</p>'
        return ""

    for cleaned_line in cleaned_lines:
        if cleaned_line.startswith("###"):
            compiled_html += flush_paragraph()
            current_paragraph_lines = []
            header_title = cleaned_line.replace("###", "").strip()
            compiled_html += f'<h3 style="color: #1D3557; border-bottom: 2px solid #E5E5E5; padding-bottom: 6px; margin-top: 28px; margin-bottom: 12px; font-size: 20px; font-weight: bold; letter-spacing: 0.5px;">{header_title}</h3>'
            
        elif cleaned_line.startswith("##"):
            compiled_html += flush_paragraph()
            current_paragraph_lines = []
            header_title = cleaned_line.replace("##", "").strip()
            compiled_html += f'<h2 style="color: #1D3557; border-bottom: 2px solid #CED4DA; padding-bottom: 8px; margin-top: 32px; margin-bottom: 16px; font-size: 24px; font-weight: bold;">{header_title}</h2>'
        
        elif "SECTION" in cleaned_line.upper() or "SUMMARY" in cleaned_line.upper():
            compiled_html += flush_paragraph()
            current_paragraph_lines = []
            clean_section_title = re.sub(r"^[\s\-_*•▪▫◦¶.·\d]+", "", cleaned_line).strip()
            clean_section_title = clean_section_title.replace("—", "").replace("-", "").strip()
            compiled_html += f'<h4 style="color: #1D3557; font-size: 17px; font-weight: bold; margin-top: 26px; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.5px; border-left: 4px solid #1D3557; padding-left: 8px;">{clean_section_title}</h4>'

        elif cleaned_line.startswith("*") or cleaned_line.startswith("•"):
            compiled_html += flush_paragraph()
            current_paragraph_lines = []
            list_item_text = re.sub(r"^[\s\-_*•▪▫◦¶.·\d]+", "", cleaned_line).strip()
            compiled_html += f'<div style="text-align: justify; text-justify: inter-word; font-size: 14px; color: #495057; line-height: 1.5; margin-left: 40px; margin-bottom: 8px; display: list-item; list-style-type: circle;">{list_item_text}</div>'
            
        elif cleaned_line.startswith("-") or re.match(r"^\d+\.", cleaned_line):
            compiled_html += flush_paragraph()
            current_paragraph_lines = []
            list_item_text = re.sub(r"^[\s\-_*•▪▫◦¶.·\d]+", "", cleaned_line).strip()
            compiled_html += f'<div style="text-align: justify; text-justify: inter-word; font-size: 15px; color: #212529; line-height: 1.5; margin-left: 20px; margin-bottom: 12px; display: list-item; list-style-type: square; font-weight: bold;">{list_item_text}</div>'
            
        else:
            current_paragraph_lines.append(cleaned_line)
            
    compiled_html += flush_paragraph()
    st.markdown(compiled_html, unsafe_allow_html=True)
def render_status_card(label, current_value):
    """Paints clean executive control cards with HTML injection based on the original semantics."""
    val_str = str(current_value).upper().strip()
    if "AGREED" in val_str or "LOCKED" in val_str or "CLOSED" in val_str:
        status_text = "Agreed & Locked"
        bg_color = "#E8F5E9"
        border_color = "#4CAF50"
        text_color = "#1B5E20"
        badge_html = '<span style="background-color: #4CAF50; color: white; padding: 3px 8px; border-radius: 10px; font-size: 11px; font-weight: bold;">\u25cc Agreed</span>'
    elif "DISCUSSION" in val_str or "UNDER" in val_str:
        status_text = "Under Active Debate"
        bg_color = "#FFFDE7"
        border_color = "#FBC02D"
        text_color = "#F57F17"
        badge_html = '<span style="background-color: #FBC02D; color: black; padding: 3px 8px; border-radius: 10px; font-size: 11px; font-weight: bold;">\u25cc Discussing</span>'
    else:
        status_text = "Not Discussed Yet"
        bg_color = "#F8F9FA"
        border_color = "#CED4DA"
        text_color = "#6C757D"
        badge_html = '<span style="background-color: #6C757D; color: white; padding: 3px 8px; border-radius: 10px; font-size: 11px; font-weight: bold;">\u25cb Untouched</span>'

    st.markdown(f"""
    <div style="background-color: {bg_color}; border-left: 5px solid {border_color}; padding: 12px; border-radius: 4px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="font-size: 12px; color: #495057; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px;">{label}</div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px;">
            <span style="font-size: 14px; font-weight: 600; color: {text_color};">{status_text}</span>
            {badge_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

def run_parallel_observer_audit(chat_history_list, current_metrics, case_keys):
    if not chat_history_list or not case_keys:
        return current_metrics
        
    updated_metrics = current_metrics.copy()
    short_window_history = chat_history_list[-6:]
    transcript_text = "".join([f"{turn['role'].upper()}: {turn['content']}\n" for turn in short_window_history])
    slots_blueprint = "{\n" + ",\n".join([f'  "{k}": "UNDER_DISCUSSION o AGREED o REJECTED_OR_OPEN o UNTOUCHED"' for k in case_keys]) + "\n}"
    
    observer_system_prompt = f"""
    You are an expert, cold, and highly precise corporate contract observer AI. Your sole job is to monitor a live business negotiation chat transcript and log the status of the contract package.
    ACTIVE PARAMETERS LOG MATRIX TO TRACK: {case_keys}
    STRICT COMPLIANCE INSTRUCTIONS:
    Analyze the recent short transcript window to evaluate the state of EACH variable completely separate from the others.
    Never group variables. Evaluate them one by one.
    OUTPUT MANDATE: Return ONLY a clean JSON object. Do not include markdown tags or preambles.
    {slots_blueprint}
    """
    try:
        raw_audit_text = safe_mistral_call([
            {"role": "system", "content": observer_system_prompt},
            {"role": "user", "content": f"Here is the recent meeting transcript window to audit:\n{transcript_text}"}
        ], temperature=0.0)
        
        clean_audit_json = re.sub(r"```json|```", "", raw_audit_text).strip()
        parsed_audit = json.loads(clean_audit_json)
        normalized_audit = {str(k).strip().lower(): v for k, v in parsed_audit.items()}
        
        for slot in case_keys:
            slot_clean = str(slot).strip()
            slot_key_lower = slot_clean.lower()
            verdict = str(normalized_audit.get(slot_key_lower, "UNTOUCHED")).upper().strip()
            
            if "AGREED" in verdict:
                updated_metrics[slot_clean] = "AGREED_AND_LOCKED"
            elif "REJECTED" in verdict or "OPEN" in verdict:
                updated_metrics[slot_clean] = "UNDER_DISCUSSION"
            elif "DISCUSSION" in verdict:
                if "AGREED" not in str(updated_metrics.get(slot_clean, "")).upper():
                    updated_metrics[slot_clean] = "UNDER_DISCUSSION"
            else:
                if slot_clean not in updated_metrics:
                    updated_metrics[slot_clean] = "UNTOUCHED"
    except Exception:
        return current_metrics
    return updated_metrics

# Global state initialization
if "phase" not in st.session_state: st.session_state.phase = "setup"
if "history" not in st.session_state: st.session_state.history = []
if "turn_counter" not in st.session_state: st.session_state.turn_counter = 0
if "ai_context" not in st.session_state: st.session_state.ai_context = ""
if "user_instructions" not in st.session_state: st.session_state.user_instructions = ""
if "ai_profile" not in st.session_state: st.session_state.ai_profile = "Medium"
if "current_metrics" not in st.session_state: st.session_state.current_metrics = {}
if "case_keys" not in st.session_state: st.session_state.case_keys = []
# ========================================================================
# --- PHASE 1: INITIALIZATION SUITE (MODULE SHUTS DOWN AFTER SETUP) ---
# ========================================================================
if st.session_state.phase == "setup":
    st.title("🤝 Executive Negotiation & Soft Skills Simulator")
    case_source = st.radio("Choose Case Origin:", ["Select from Previously Created Cases", "Create New Custom Case Study"])
    selected_file_case = None
    topic = ""
    
    if case_source == "Select from Previously Created Cases":
        os.makedirs("development_cases", exist_ok=True)
        available_files = [f for f in os.listdir("development_cases") if f.endswith("_user.txt")]
        if available_files:
            selected_file_case = st.selectbox("Choose available local case:", sorted(list(set([f.replace("_user.txt", "") for f in available_files]))))
        else:
            st.warning("No cases found inside 'development_cases/'. Please switch to creation mode.")
            selected_file_case = None
    else:
        topic = st.text_area("What do you want to negotiate today?", placeholder="Example: Commercial office lease...")
    
    ai_profile = st.selectbox("Define opponent strategic profile:", ["Soft (Accommodating & Proactive)", "Medium (Pragmatic & Firm)", "Hard (Aggressive & Anchored)"])
    
    if st.button("Open Boardroom & Load Strategic Case", use_container_width=True):
        st.session_state.ai_profile = ai_profile
        os.makedirs("development_cases", exist_ok=True)
        
        if case_source == "Create New Custom Case Study":
            texto_limpio = topic.strip()
            if len(texto_limpio) < 5:
                with st.spinner("🎲 Generating random premium scenario description..."):
                    prompt_random = "Generate a short, 1-sentence highly sophisticated corporate negotiation scenario description. Output only the sentence."
                    texto_limpio = safe_mistral_call([{"role": "user", "content": prompt_random}]).strip()
                    st.info(f"🎲 Random Scenario Isolated: {texto_limpio}")

            with st.status("🚀 Advanced Pipeline: Processing Macroeconomic Model...", expanded=True) as status:
                status.update(label="🧠 Stage 1/4: Identifying variables and computing economic curves...", state="running")
                base_prompt = st.secrets["PROMPT_GENERACION"]
                
                # Proteger las llaves del macro-modelo matemático usando reemplazo directo en lugar de .format()
                prompt_inyectado = base_prompt.replace("{tema}", texto_limpio)
                raw_content = safe_mistral_call([{"role": "user", "content": prompt_inyectado}], temperature=0.7)

                status.update(label="⚖️ Stage 2/4: Executing Critical Auto-Correction Loop (HBS Checklist)...", state="running")
                prompt_auditoria = (
                    f"You are a Senior Corporate Case Auditor. Review, optimize, and audit this layout:\n\n{raw_content}\n\n"
                    f"CRITICAL COMPLIANCE REQUIREMENT: You MUST preserve the exact encapsulation tags (START_USER_DATA, END_USER_DATA, "
                    f"START_AI_SECRET_DATA, END_AI_SECRET_DATA) in your final response. Output ONLY the corrected case study enclosed inside those tags."
                )
                content_verificado = safe_mistral_call([{"role": "user", "content": prompt_auditoria}], temperature=0.1)
                
                status.update(label="🗜️ Stage 3/4: Decompressing Ledger Data Wall...", state="running")
                try:
                    match_user = re.search(r"START_USER_DATA(.*?)END_USER_DATA", content_verificado, re.DOTALL)
                    match_ai = re.search(r"START_AI_SECRET_DATA(.*?)END_AI_SECRET_DATA", content_verificado, re.DOTALL)
                    
                    if match_user and match_ai:
                        st.session_state.user_instructions = match_user.group(1).replace("USER_BLOCK", "").strip()
                        st.session_state.ai_context = match_ai.group(1).replace("AI_BLOCK", "").strip()
                    else:
                        keyword_ai = "START_AI_SECRET_DATA" if "START_AI_SECRET_DATA" in content_verificado else "AI_BLOCK"
                        if keyword_ai in content_verificado:
                            parts = content_verificado.split(keyword_ai, 1)
                            st.session_state.user_instructions = parts.replace("START_USER_DATA", "").replace("END_USER_DATA", "").replace("USER_BLOCK", "").strip()
                            st.session_state.ai_context = parts.replace("END_AI_SECRET_DATA", "").replace("AI_BLOCK", "").strip()
                        else:
                            st.session_state.user_instructions = content_verificado.strip()
                            st.session_state.ai_context = "Error parsing AI context. Stay in character as a tough corporate negotiator."
                    
                    safe_filename = re.sub(r'[^a-zA-Z0-9_]', '_', texto_limpio[:15]).lower()
                    palabra_clave = f"{safe_filename}_{int(time.time())}"
                    with open(f"development_cases/{palabra_clave}_user.txt", "w", encoding="utf-8") as f: f.write(st.session_state.user_instructions)
                    with open(f"development_cases/{palabra_clave}_ai.txt", "w", encoding="utf-8") as f: f.write(st.session_state.ai_context)
                    status.update(label="🤝 Stage 4/4: Strategic matrix successfully calibrated.", state="complete")
                except Exception as e:
                    st.error(f"Failed to parse matrix layout: {e}"); st.stop()
        else:
            with open(f"development_cases/{selected_file_case}_user.txt", "r", encoding="utf-8") as f: st.session_state.user_instructions = f.read().strip()
            with open(f"development_cases/{selected_file_case}_ai.txt", "r", encoding="utf-8") as f: st.session_state.ai_context = f.read().strip()
            st.toast("🎯 Historical case study loaded successfully.")
            
        discovery_prompt = f"Identify exactly 5 variables negotiated: {st.session_state.ai_context}. Return ONLY a raw JSON list of their 5 plain text names."
        try:
            raw_json_keys = safe_mistral_call([{"role": "user", "content": discovery_prompt}])
            clean_json_keys = re.sub(r"```json|```", "", raw_json_keys).strip()
            st.session_state.case_keys = json.loads(clean_json_keys)[:5]
        except Exception:
            st.session_state.case_keys = ["Base Price Structure", "Service Level Agreement (SLA)", "Transition Timeline", "Intellectual Property Rights", "Termination Clauses"]
        
        st.session_state.current_metrics = {str(k).strip(): "UNTOUCHED" for k in st.session_state.case_keys}
        
        with st.spinner("🤝 Stage 3/3: Dispatching executive opening bubble..."):
            profile_instructions = "friendly, highly cooperative" if "Soft" in ai_profile else ("extremely aggressive, unyielding" if "Hard" in ai_profile else "balanced, corporate")
            prompt_intro = f"Based on your role: {st.session_state.ai_context}. Write a professional 2-sentence opening statement to start the meeting. Tone: {profile_instructions}."
            try:
                raw_greetings = safe_mistral_call([{"role": "user", "content": prompt_intro}])
                greetings_text = re.sub(r"^(Here's|Here is|Sure|As requested|Adhering).*?:", "", raw_greetings, flags=re.IGNORECASE).strip()
                if not greetings_text: greetings_text = raw_greetings.replace('"', '')
            except Exception:
                greetings_text = "Good day. Let us open the floor to analyze the financial parameters of this contract."

            st.session_state.history.append({"role": "assistant", "content": greetings_text})
            st.session_state.phase = "chat"
            st.rerun()
            st.stop()
# ========================================================================
# --- PHASE 2: LIVE SIMULATION INTERACTION (BOARDROOM CHAT) ---
# ========================================================================
elif st.session_state.phase == "chat" and st.session_state.turn_counter < 20:
    st.title("💼 Live Negotiation Room - Executive Boardroom")
    st.progress(st.session_state.turn_counter / 20)
    
    with st.sidebar:
        st.markdown("<style>[data-testid='stSidebarUserContent'] { padding-top: 1rem !important; }</style>", unsafe_allow_html=True)
        st.markdown("### Strategic Meeting Timeline")
        st.metric(label="Rounds Spent", value=f"{st.session_state.turn_counter} / 20")
        enable_monitoring = st.toggle("Enable Real-Time Tracker AI", value=True)
        st.markdown("### Live Contract Tracker")
        for label, val in st.session_state.current_metrics.items(): render_status_card(label, val)

    with st.expander("📋 Review Confidential Character Instructions", expanded=False): 
        render_justified_report(st.session_state.user_instructions)

    st.divider()
    for msg in st.session_state.history:
        visible_text = re.sub(r"DATA_STREAM:\s*\{.*?\}", "", msg["content"], flags=re.DOTALL).strip()
        if visible_text:
            with st.chat_message(msg["role"]): st.write(visible_text)
            
    if user_input := st.chat_input(placeholder="Type your counteroffer or package proposal here..."):
        if user_input.strip().lower() == "/end":
            st.session_state.phase = "feedback"
            st.rerun()
            st.stop()
            
        st.session_state.history.append({"role": "user", "content": user_input})
        st.session_state.turn_counter += 1
        
        with st.chat_message("user"):
            st.write(user_input)
        
        with st.chat_message("assistant"):
            with st.spinner("Counterpart is typing..."):
                profile_rules = "Personality: Brutal, unyielding." if "Hard" in st.session_state.ai_profile else ("Personality: Accommodating." if "Soft" in st.session_state.ai_profile else "Personality: Pragmatic.")
                system_instruction = f"""You are the corporate character: {st.session_state.ai_context}
                Profile: {profile_rules}
                ⚠️ NEGOTIATION WALL MANDATE: NEVER mention dEBITDA or systems logic.
                Append at the absolute end: DATA_STREAM: {{"v1_price": 3.0}}"""
                
                messages_payload = [{"role": "system", "content": system_instruction}]
                for turn in st.session_state.history:
                    if turn.get("content", "").strip(): messages_payload.append({"role": turn["role"], "content": turn["content"]})
                
                # Chat protegido en tiempo real de forma segura contra el error 429
                ai_raw_text = safe_mistral_call(messages_payload, temperature=0.7)
                
                if enable_monitoring:
                    time.sleep(1.5) # Pausa mínima para no congestionar las peticiones por segundo
                    st.session_state.current_metrics = run_parallel_observer_audit(st.session_state.history + [{"role": "assistant", "content": ai_raw_text}], st.session_state.current_metrics, st.session_state.case_keys)
                
                st.session_state.history.append({"role": "assistant", "content": ai_raw_text})
        st.rerun()
        st.stop()

    st.markdown("---")
    if st.text_input("🔑 Developer Auditing Mode", type="password", key="chat_admin_field") == "admin123":
        st.success("Ground Truth Matrix:")
        render_justified_report(st.session_state.ai_context)

# ========================================================================
# --- PHASE 3: COMPREHENSIVE PERFORMANCE REVIEW (MBA REPORT) ---
# ========================================================================
elif st.session_state.phase == "feedback" or st.session_state.turn_counter >= 20:
    st.title("Executive Strategic Evaluation & Soft Skills Audit")
    if st.session_state.current_metrics:
        with st.expander("Final Registered Contract Package Status", expanded=True):
            for label, val in st.session_state.current_metrics.items(): render_status_card(label, val)
            
    loading_placeholder = st.empty()
    loading_placeholder.progress(0.65, text="🤖 Processing transcript timeline streams & behavioral maturity matrix...")

    transcript_data = ""
    round_idx = 1
    for m in st.session_state.history:
        content_cleaned = re.sub(r"DATA_STREAM:\s*\{.*?\}", "", m["content"], flags=re.DOTALL).strip()
        transcript_data += f"Round {round_idx:02d} - {m['role'].upper()}: {content_cleaned}\n"
        if m["role"] == "assistant": round_idx += 1
        
    active_keys = list(st.session_state.current_metrics.keys())
    json_structure = ", ".join([f'"{k}": [list of integers from 0 to 7]' for k in active_keys])
    
    # 🛡️ PROTECCIÓN ANTI-SDK_ERROR: Reemplazo explícito seguro para aislar las llaves complejas del JSON
    prompt_base_fb = st.secrets["PROMPT_FEEDBACK"]
    prompt_inyectado_fb = prompt_base_fb.replace("{contexto_ia}", st.session_state.ai_context)
    prompt_inyectado_fb = prompt_inyectado_fb.replace("{transcripcion}", transcript_data)
    prompt_inyectado_fb = prompt_inyectado_fb.replace("{active_variables_instruction}", f"TIMELINE_STREAM: {{{json_structure}}}")
    
    try:
        # Petición masiva final del informe analítico protegida contra interrupciones de red
        raw_feedback = safe_mistral_call([{"role": "user", "content": prompt_inyectado_fb}], temperature=0.3)
        loading_placeholder.empty()

        timeline_data = {}
        timeline_match = re.search(r"TIMELINE_STREAM:\s*(\{.*?\})", raw_feedback)
        if timeline_match:
            try: timeline_data = json.loads(timeline_match.group(1))
            except Exception: pass
            
        clean_feedback = re.sub(r"TIMELINE_STREAM:\s*\{.*?\}", "", raw_feedback, flags=re.DOTALL).strip().replace("```markdown", "").replace("```", "").strip()
        
        st.markdown("### Negotiation Process Lifecycle Chart")
        if timeline_data:
            try:
                df_timeline = pd.DataFrame(timeline_data)
                df_timeline.index = [f"Round {i+1:02d}" for i in range(len(df_timeline))]
                st.line_chart(df_timeline, use_container_width=True)
            except Exception: st.write(timeline_data)
                
        st.divider()
        st.markdown("### Executive Soft Skills Audit & Report")
        render_justified_report(clean_feedback)
        
        compiled_master_report = f"=== Master Audit Archive ===\n\nTranscript:\n{transcript_data}\n\nReport:\n{clean_feedback}"
        st.download_button(label="💾 Download Full Report Archive (.txt)", data=compiled_master_report, file_name="negotiation_archive.txt", mime="text/plain", use_container_width=True)
    except Exception as e:
        loading_placeholder.empty()
        st.error(f"Error generating analytical report: {e}")

    if st.button("🔄 Start New Negotiation Session", use_container_width=True):
        st.session_state.clear()
        st.rerun()
        st.stop()

import streamlit as st
from zhipuai import ZhipuAI
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

# Secure initialization of the native ZhipuAI client using Streamlit secrets
@st.cache_resource
def get_zhipu_client():
    return ZhipuAI(api_key=st.secrets["ZHIPUAI_API_KEY"])

client = get_zhipu_client()

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
        
        # 🛡️ FILTRO ABSOLUTO ANTI-RUIDO VISUAL: 
        # Si la línea está vacía o contiene SOLAMENTE símbolos, puntos de lista (•, ▪, -, *), 
        # o caracteres no alfanuméricos sueltos, la eliminamos por completo.
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
        # 1. ENCABEZADOS PRINCIPALES DE MARKDOWN (##, ###)
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
        
        # 2. SECCIONES O SUMARIOS EJECUTIVOS (Garantizado sin puntos ni viñetas)
        elif "SECTION" in cleaned_line.upper() or "SUMMARY" in cleaned_line.upper():
            compiled_html += flush_paragraph()
            current_paragraph_lines = []
            # Removemos de forma estricta cualquier marcador que esté pegado al título
            clean_section_title = re.sub(r"^[\s\-_*•▪▫◦¶.·\d]+", "", cleaned_line).strip()
            clean_section_title = clean_section_title.replace("—", "").replace("-", "").strip()
            compiled_html += f'<div style="color: #1D3557; font-size: 17px; font-weight: bold; margin-top: 26px; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.5px; border-left: 4px solid #1D3557; padding-left: 8px;">{clean_section_title}</div>'

        # 3. OPCIONES DE LAS VARIABLES (Sangría profunda de 40px y viñeta redonda)
        elif cleaned_line.startswith("*") or cleaned_line.startswith("•"):
            compiled_html += flush_paragraph()
            current_paragraph_lines = []
            list_item_text = re.sub(r"^[\s\-_*•▪▫◦¶.·\d]+", "", cleaned_line).strip()
            compiled_html += f'<div style="text-align: justify; text-justify: inter-word; font-size: 14px; color: #495057; line-height: 1.5; margin-left: 40px; margin-bottom: 8px; display: list-item; list-style-type: circle;">{list_item_text}</div>'
            
        # 4. VARIABLES PRINCIPALES (Sangría de 20px, negrita y viñeta cuadrada)
        elif cleaned_line.startswith("-") or re.match(r"^\d+\.", cleaned_line):
            compiled_html += flush_paragraph()
            current_paragraph_lines = []
            list_item_text = re.sub(r"^[\s\-_*•▪▫◦¶.·\d]+", "", cleaned_line).strip()
            compiled_html += f'<div style="text-align: justify; text-justify: inter-word; font-size: 15px; color: #212529; line-height: 1.5; margin-left: 20px; margin-bottom: 12px; display: list-item; list-style-type: square; font-weight: bold;">{list_item_text}</div>'
            
        else:
            # Acumulador de prosa normal y narrativa fluida
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
        
    transcript_text = ""
    for turn in short_window_history:
        transcript_text += f"{turn['role'].upper()}: {turn['content']}\n"
        
    slots_blueprint = "{\n" + ",\n".join([f'  "{k}": "UNDER_DISCUSSION o AGREED o REJECTED_OR_OPEN o UNTOUCHED"' for k in case_keys]) + "\n}"
    
    observer_system_prompt = f"""
    You are an expert, cold, and highly precise corporate contract observer AI. Your sole job is to monitor a live business negotiation chat transcript and log the status of the contract package.
    ACTIVE PARAMETERS LOG MATRIX TO TRACK: {case_keys}
    
    STRICT COMPLIANCE INSTRUCTIONS:
    Analyze the recent short transcript window to evaluate the state of EACH variable completely separate from the others:
    1. If a specific variable has NOT been mentioned or touched within this recent exchange, rate it as "UNTOUCHED".
    2. If a specific variable is actively being proposed, counter-offered, or under open debate by either side in these recent lines, rate it as "UNDER_DISCUSSION".
    3. SPECIAL GREEN HANDSHAKE RULE: You MUST ONLY rate a variable as "AGREED" if one party made a concrete offer in a previous turn, AND the other party has explicitly, verbally, and unambiguously accepted THAT EXACT VALUE for THAT SPECIFIC variable in a subsequent turn.
    4. CRITICAL REVERSION MANDATE: If a party explicitly rejects, backs out, or clarifies they DID NOT agree to a variable previously discussed (e.g., "I didn't agree to that duration yet", "No, that is still open", "We need to reopen the pricing discussion"), you MUST rate that specific variable as "REJECTED_OR_OPEN".
    
    Never group variables. Evaluate them one by one.
    OUTPUT MANDATE: Return ONLY a clean JSON object following this exact template structure layout. Do not include markdown format tags, preambles, descriptions, or feedback.
    {slots_blueprint}
    """
    
    try:
        response_audit = client.chat.completions.create(
            model='glm-4-flash',
            messages=[
                {"role": "system", "content": observer_system_prompt},
                {"role": "user", "content": f"Here is the recent meeting transcript window to audit:\n{transcript_text}"}
            ],
            temperature=0.0
        )
        # VERIFICADO: Conserva el [0] requerido para el entorno local en el modelo Flash
        raw_audit_text = response_audit.choices[0].message.content.strip()
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
    
    if st.button("Open Boardroom & Load Strategic Case", width='stretch'):
        st.session_state.ai_profile = ai_profile
        os.makedirs("development_cases", exist_ok=True)
        
        if case_source == "Create New Custom Case Study":
            texto_limpio = topic.strip()
            if len(texto_limpio) < 5:
                with st.spinner("🎲 Generating random premium scenario description..."):
                    prompt_random = "Generate a short, 1-sentence highly sophisticated corporate negotiation scenario description. Output only the sentence."
                    response_tema = client.chat.completions.create(model='glm-4.5-air', messages=[{"role": "user", "content": prompt_random}])
                    # VERIFICADO: Conserva el [0] requerido por tu entorno para el modelo 4.5
                    texto_limpio = response_tema.choices[0].message.content.strip()
                    st.info(f"🎲 Random Scenario Isolated: {texto_limpio}")

            # REPARADO: Todo el log de st.status ahora se muestra en estricto inglés
            with st.status("🚀 Advanced Pipeline: Processing Macroeconomic Model...", expanded=True) as status:
                status.update(label="🧠 Stage 1/4: Identifying variables and computing economic curves...", state="running")
                base_prompt = st.secrets["PROMPT_GENERACION"]
                response = client.chat.completions.create(model='glm-4.5-air', messages=[{"role": "user", "content": base_prompt.format(tema=texto_limpio)}])
                # VERIFICADO: Conserva el [0] requerido por tu entorno para el modelo 4.5
                raw_content = response.choices[0].message.content

                status.update(label="⚖️ Stage 2/4: Executing Critical Auto-Correction Loop (HBS Checklist)...", state="running")
                # REPARADO: Se blinda el prompt del auditor para que no mutile ni reescriba las etiquetas estructurales
                prompt_auditoria = (
                    f"You are a Senior Corporate Case Auditor. Review, optimize, and audit this layout:\n\n{raw_content}\n\n"
                    f"CRITICAL COMPLIANCE REQUIREMENT: You MUST preserve the exact encapsulation tags (START_USER_DATA, END_USER_DATA, "
                    f"START_AI_SECRET_DATA, END_AI_SECRET_DATA) in your final response. Do not output meta-text or external summaries. "
                    f"Output ONLY the corrected case study enclosed inside those mandatory structural markup tags."
                )
                response_auditada = client.chat.completions.create(model='glm-4.5-air', messages=[{"role": "user", "content": prompt_auditoria}], temperature=0.1)
                # VERIFICADO: Conserva el [0] requerido por tu entorno para el modelo 4.5
                content_verificado = response_auditada.choices[0].message.content
                
                status.update(label="🗜️ Stage 3/4: Decompressing Ledger Data Wall...", state="running")
                try:
                    match_user = re.search(r"START_USER_DATA(.*?)END_USER_DATA", content_verificado, re.DOTALL)
                    match_ai = re.search(r"START_AI_SECRET_DATA(.*?)END_AI_SECRET_DATA", content_verificado, re.DOTALL)
                    
                    if match_user and match_ai:
                        st.session_state.user_instructions = match_user.group(1).replace("USER_BLOCK", "").strip()
                        st.session_state.ai_context = match_ai.group(1).replace("AI_BLOCK", "").strip()
                    else:
                        # CORREGIDO: Fallback robusto indexando la posición de los strings para evitar romper la lista 'parts'
                        keyword_ai = "START_AI_SECRET_DATA" if "START_AI_SECRET_DATA" in content_verificado else "AI_BLOCK"
                        if keyword_ai in content_verificado:
                            parts = content_verificado.split(keyword_ai, 1)
                            raw_user = parts[0]
                            raw_ai = parts[1]
                            st.session_state.user_instructions = raw_user.replace("START_USER_DATA", "").replace("END_USER_DATA", "").replace("USER_BLOCK", "").strip()
                            st.session_state.ai_context = raw_ai.replace("END_AI_SECRET_DATA", "").replace("AI_BLOCK", "").strip()
                        else:
                            st.session_state.user_instructions = content_verificado.strip()
                            st.session_state.ai_context = "Error parsing AI context. Stay in character as a tough corporate negotiator."
                    
                    safe_filename = re.sub(r'[^a-zA-Z0-9_]', '_', texto_limpio[:15]).lower()
                    palabra_clave = f"{safe_filename}_{int(time.time())}"
                    with open(f"development_cases/{palabra_clave}_user.txt", "w", encoding="utf-8") as f: 
                        f.write(st.session_state.user_instructions)
                    with open(f"development_cases/{palabra_clave}_ai.txt", "w", encoding="utf-8") as f: 
                        f.write(st.session_state.ai_context)
                    status.update(label="🤝 Stage 4/4: Strategic matrix successfully calibrated.", state="complete")
                except Exception as e:
                    st.error(f"Failed to parse matrix layout: {e}"); st.stop()
        else:
            # CORREGIDO: Modo lectura 'r' emparejado estrictamente con f.read() para no lanzar UnsupportedOperation
            with open(f"development_cases/{selected_file_case}_user.txt", "r", encoding="utf-8") as f: 
                st.session_state.user_instructions = f.read().strip()
            with open(f"development_cases/{selected_file_case}_ai.txt", "r", encoding="utf-8") as f: 
                st.session_state.ai_context = f.read().strip()
            st.toast("🎯 Historical case study loaded successfully.")
        discovery_prompt = f"Identify exactly 5 variables negotiated: {st.session_state.ai_context}. Return ONLY a raw JSON list of their 5 plain text names."
        try:
            response_keys = client.chat.completions.create(model='glm-4-flash', messages=[{"role": "user", "content": discovery_prompt}])
            # VERIFICADO: Conserva el [0] requerido por tu entorno para el modelo Flash
            raw_json_keys = response_keys.choices[0].message.content.strip()
            clean_json_keys = re.sub(r"```json|```", "", raw_json_keys).strip()
            st.session_state.case_keys = json.loads(clean_json_keys)[:5]
        except Exception:
            st.session_state.case_keys = ["Base Price Structure", "Service Level Agreement (SLA)", "Transition Timeline", "Intellectual Property Rights", "Termination Clauses"]
        
        st.session_state.current_metrics = {str(k).strip(): "UNTOUCHED" for k in st.session_state.case_keys}
        
        with st.spinner("🤝 Stage 3/3: Dispatching executive opening bubble..."):
            profile_instructions = "friendly, highly cooperative" if "Soft" in ai_profile else ("extremely aggressive, unyielding" if "Hard" in ai_profile else "balanced, corporate")
            prompt_intro = f"Based on your role: {st.session_state.ai_context}. Write a professional 2-sentence opening statement to start the meeting. Tone: {profile_instructions}."
            
            try:
                response_intro = client.chat.completions.create(
                    model='glm-4.5-air', 
                    messages=[{"role": "user", "content": prompt_intro}]
                )
                # VERIFICADO: Conserva el [0] requerido por tu entorno para el modelo 4.5
                raw_greetings = response_intro.choices[0].message.content.strip()
                greetings_text = re.sub(r"^(Here's|Here is|Sure|As requested|Adhering).*?:", "", raw_greetings, flags=re.IGNORECASE).strip()
                
                if not greetings_text:
                    greetings_text = raw_greetings.replace('"', '')
            except Exception:
                greetings_text = "Good day. Let us open the floor to analyze the financial parameters of this contract."

            st.session_state.history.append({"role": "assistant", "content": greetings_text})
            st.session_state.phase = "chat"
            st.rerun()
            # REPARADO: Detiene el flujo de forma tajante para evitar que Streamlit siga ejecutando el script y pinte el reporte antes de jugar
            st.stop()
# ========================================================================
# --- PHASE 2: LIVE SIMULATION INTERACTION (BOARDROOM CHAT) ---
# ========================================================================
elif st.session_state.phase == "chat" and st.session_state.turn_counter < 20:
    st.title("💼 Live Negotiation Room - Executive Boardroom")
    st.progress(st.session_state.turn_counter / 20)
    
    with st.sidebar:
        st.markdown("<style>[data-testid='stSidebarUserContent'] { padding-top: 1rem !important; } .stCheckbox, .stToggle { margin-bottom: -10px !important; }</style>", unsafe_allow_html=True)
        st.markdown("### Strategic Meeting Timeline")
        st.metric(label="Rounds Spent", value=f"{st.session_state.turn_counter} / 20")
        enable_monitoring = st.toggle("Enable Real-Time Tracker AI", value=True)
        st.markdown("### Live Contract Tracker")
        for label, val in st.session_state.current_metrics.items(): 
            render_status_card(label, val)

    with st.expander("📋 Review Confidential Character Instructions", expanded=False): 
        # We invoke your custom layout engine to render fully justified text
        render_justified_report(st.session_state.user_instructions)

    st.divider()
    
    for msg in st.session_state.history:
        visible_text = re.sub(r"DATA_STREAM:\s*\{.*?\}", "", msg["content"], flags=re.DOTALL).strip()
        if visible_text:
            with st.chat_message(msg["role"]): 
                st.write(visible_text)
            
    if user_input := st.chat_input(placeholder="Type your counteroffer or package proposal here... (Or type /end to close meeting)"):
        if user_input.strip().lower() == "/end":
            st.session_state.phase = "feedback"
            st.rerun()
            st.stop()
            
        st.session_state.history.append({"role": "user", "content": user_input})
        st.session_state.turn_counter += 1
        
        with st.chat_message("user"): 
            st.write(user_input)
        
        with st.chat_message("assistant"):
            with st.spinner("Counterpart is typing a response..."):
                if "Soft" in st.session_state.ai_profile:
                    profile_rules = (
                        "Template Personality: Accommodating, friendly, and polite. "
                        "CRITICAL TACTICAL TRIGGER: If the user states they are tired, frustrated, unhappy, or threatens to leave/stop negotiating, "
                        "do NOT give up and do NOT end the meeting blindly. Instead, express deep empathy, state that you value their business, "
                        "and PROACTIVELY offer a moderate concession or a slightly better counteroffer on a secondary variable to keep them engaged "
                        "and save the deal, without giving away all your profit at once."
                    )
                elif "Hard" in st.session_state.ai_profile:
                    profile_rules = "Personality: Brutal, unyielding, and aggressive. Uses extreme anchoring."
                else:
                    profile_rules = "Personality: Pragmatic, analytical, and fair."
                
                system_instruction = f"""
                You are the corporate negotiator character. Your confidential corporate background and operational boundaries are defined here: 
                {st.session_state.ai_context}
                
                Profile style/Personality rules: {profile_rules}
                
                ⚠️ NEGOTIATION WALL MANDATE (NEVER BREAK THIS):
                1. You are a human executive in a high-stakes business meeting. You do NOT know what an LLM, a prompt, or a 'Negotiation Matrix' is.
                2. NEVER, under any circumstance, mention technical terms like "dEBITDA", "EBITDA impact", "EBITDA curves", "Level 1.0", "target of +4M", or "windfall bonus conditions".
                3. NEVER reveal your exact underlying financial values, your exact reservation points, or the numerical penalty/synergy math driving your choices.
                4. Talk strictly in strategic business prose. If you want to argue about price, duration, or exclusivity, use business arguments (e.g., "market volatility", "long-term commitment", "operational overhead"), NEVER the mathematical ledger score.
                
                # --- MANDATORY ATTACHMENT REGEX AND API RUNNERS ---
                CRITICAL ATTACHMENT MANDATE: Append a hidden JSON line at the absolute end (do not mention it in your dialogue):
                DATA_STREAM: {{"v1_price": value, "v2_metric": value, "v3_metric": value, "v4_metric": value, "v5_metric": value}} (Values 1.0 to 5.0)
                """
                
                messages_payload = [{"role": "system", "content": system_instruction}]
                for turn in st.session_state.history:
                    clean_role = str(turn.get("role", "user")).strip()
                    clean_content = str(turn.get("content", "")).strip()
                    if clean_content: 
                        messages_payload.append({"role": clean_role, "content": clean_content})
                
                try:
                    ai_response = client.chat.completions.create(model='glm-4.5-air', messages=messages_payload, temperature=0.7)
                    # CORRECCIÓN DE INDEXADO: Se restaura el [0] mandatorio exigido por tu entorno local
                    ai_raw_text = ai_response.choices[0].message.content
                except Exception as api_error:
                    ai_raw_text = f"🚨 [API Failure Diagnostic Log - Details: {str(api_error)}]"
                
                if enable_monitoring:
                    st.session_state.current_metrics = run_parallel_observer_audit(
                        st.session_state.history + [{"role": "assistant", "content": ai_raw_text}], 
                        st.session_state.current_metrics, 
                        st.session_state.case_keys
                    )
                
                st.session_state.history.append({"role": "assistant", "content": ai_raw_text})
                visible_clean_text = re.sub(r"DATA_STREAM:\s*\{.*?\}", "", ai_raw_text, flags=re.DOTALL).strip()
                st.write(visible_clean_text)
        st.rerun()
        st.stop()

    # ========================================================================
    # 🔑 DEVELOPER AUDITING SUITE (ENCAPSULADO DENTRO DEL CHAT ACTIVO)
    # ========================================================================
    st.markdown("---")
    admin_password = st.text_input("🔑 Developer Auditing Mode", type="password", key="chat_admin_field")
    if admin_password == "admin123":
        st.success("Access Granted - Ground Truth Matrix (AI Hidden Instructions):")
        # RENDERIZADO EJECUTIVO JUSTIFICADO: Sincronizado sin puntos extraños ni distorsión
        render_justified_report(st.session_state.ai_context)

# ========================================================================
# --- PHASE 3: COMPREHENSIVE PERFORMANCE REVIEW (MBA REPORT) ---
# ========================================================================
elif st.session_state.phase == "feedback" or st.session_state.turn_counter >= 20:
    st.title("Executive Strategic Evaluation & Soft Skills Audit")
    
    st.markdown("""
    <div style="background-color: #1D3557; padding: 25px; border-radius: 8px; text-align: center; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h1 style="color: #FFFFFF; font-size: 32px; font-weight: bold; margin-bottom: 8px; letter-spacing: 0.5px;">🤝 NEGOTIATION CONCLUDED</h1>
        <p style="color: #A8DADC; font-size: 18px; font-weight: 500; margin: 0; letter-spacing: 0.5px;">The boardroom session has been frozen. Initiating performance analytics.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.current_metrics:
        with st.expander("Final Registered Contract Package Status", expanded=True):
            for label, val in st.session_state.current_metrics.items(): 
                render_status_card(label, val)
    st.divider()
    
    loading_placeholder = st.empty()
    with loading_placeholder.container():
        st.markdown("""
        <div style="background-color: #F8F9FA; border-left: 5px solid #1D3557; padding: 20px; border-radius: 4px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <h4 style="color: #1D3557; margin-top:0; font-weight: bold;">🧠 AI Wharton Analytics Suite Active</h4>
            <p style="color: #495057; font-size: 14px; margin-bottom: 15px;">
                The Senior Executive Auditor is conducting a forensic audit of your dEBITDA curves, concession timing, 
                and conversational soft skills. This highly complex MBA-grade report takes approximately 45-60 seconds to compile.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.progress(0.65, text="🤖 Processing transcript timeline streams & behavioral maturity matrix...")

    transcript_data = ""
    round_idx = 1
    for m in st.session_state.history:
        content_cleaned = re.sub(r"DATA_STREAM:\s*\{.*?\}", "", m["content"], flags=re.DOTALL).strip()
        transcript_data += f"Round {round_idx:02d} - {m['role'].upper()}: {content_cleaned}\n"
        if m["role"] == "assistant": 
            round_idx += 1
        
    active_keys = list(st.session_state.current_metrics.keys())
    json_structure = ", ".join([f'"{k}": [list of integers from 0 to 7]' for k in active_keys])
    
    final_feedback_prompt = st.secrets["PROMPT_FEEDBACK"].format(
        contexto_ia=st.session_state.ai_context,
        transcripcion=transcript_data,
        active_variables_instruction=f"TIMELINE_STREAM: {{{json_structure}}}"
    )
    
    try:
        feedback_response = client.chat.completions.create(
            model='glm-4.5-air', 
            messages=[{"role": "user", "content": final_feedback_prompt}]
        )
        raw_feedback = feedback_response.choices[0].message.content
        loading_placeholder.empty()

        timeline_data = {}
        timeline_match = re.search(r"TIMELINE_STREAM:\s*(\{.*?\})", raw_feedback)
        if timeline_match:
            try: 
                timeline_data = json.loads(timeline_match.group(1))
            except Exception: 
                pass
            
        clean_feedback = re.sub(r"TIMELINE_STREAM:\s*\{.*?\}", "", raw_feedback, flags=re.DOTALL).strip()
        clean_feedback = clean_feedback.replace("```markdown", "").replace("```", "").strip()
        clean_feedback = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_feedback)
        clean_feedback = re.sub(r'([,.;:?!"\')\]])([a-zA-Z0-9])', r'\1 \2', clean_feedback)
        
        st.markdown("### Negotiation Process Lifecycle Chart")
        if timeline_data:
            try:
                df_timeline = pd.DataFrame(timeline_data)
                df_timeline.index = [f"Round {i+1:02d}" for i in range(len(df_timeline))]
                
                st.line_chart(df_timeline, use_container_width=True)
                
                st.markdown("""
                <div style="background-color: #F8F9FA; border-radius: 6px; padding: 15px; margin-top: -10px; border: 1px solid #E5E5E5;">
                    <div style="font-size: 13px; font-weight: bold; color: #1D3557; text-transform: uppercase; margin-bottom: 10px; letter-spacing: 0.5px;">📋 Chart Lifecycle Legend (Maturity Levels 0 to 7)</div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; font-size: 12px; color: #495057;">
                        <div><b>Level 0:</b> Un-discussed (Variable untouched)</div>
                        <div><b>Level 1:</b> Exploration (Initial screening)</div>
                        <div><b>Level 2:</b> Discovery (Underlying interests exposed)</div>
                        <div><b>Level 3:</b> Proposal (Numerical/text value offered)</div>
                        <div><b>Level 4:</b> Active Debate (Pivots & counteroffers)</div>
                        <div><b>Level 5:</b> Concession (Value traded or yielded)</div>
                        <div><b>Level 6:</b> Provisional (Verbal handshake baseline)</div>
                        <div><b>Level 7:</b> Closure (Locked & integrated into contract)</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception:
                st.write(timeline_data)
                
        st.divider()
        st.markdown("### Executive Soft Skills Audit & Report")
        render_justified_report(clean_feedback)
        
        compiled_master_report = f"=== Master Audit Archive ===\n\nUser Instructions:\n{st.session_state.user_instructions}\n\nOpponent Context:\n{st.session_state.ai_context}\n\nTranscript:\n{transcript_data}\n\nReport:\n{clean_feedback}"
        html_export_block = "<html><head><style>body { font-family: sans-serif; margin: 40px; line-height: 1.6; } h1 { color: #2B4C7E; } pre { background: #F8F9FA; padding: 15px; white-space: pre-wrap; }</style></head><body><h1>Master Audit Report</h1><pre>" + compiled_master_report + "</pre></body></html>"
        
        col_txt, col_pdf = st.columns(2)
        with col_txt: 
            # Antes: st.download_button(..., use_container_width=True)
            st.download_button(label="💾 Download Full Report Archive (.txt)", data=compiled_master_report, file_name="negotiation_archive.txt", mime="text/plain", width='stretch')
        with col_pdf: 
            # Antes: st.download_button(..., use_container_width=True)
            st.download_button(label="🌐 Export Full Report Archive to HTML Layout (.html)", data=html_export_block, file_name="negotiation_layout.html", mime="text/html", width='stretch')
            
    except Exception as e:
        loading_placeholder.empty()
        st.error(f"Error generating analytical report: {e}")

    # Antes: if st.button("🔄 Start New Negotiation Session", use_container_width=True):
    if st.button("🔄 Start New Negotiation Session", width='stretch'):

        st.session_state.clear()
        st.rerun()
        st.stop()

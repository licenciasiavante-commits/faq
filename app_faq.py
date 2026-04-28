import streamlit as st
import json
import google.generativeai as genai
import re

# =====================================================================
# Aplicación Web: Generador de Guías de Referencia / FAQ (Streamlit)
# Arquitectura: Cliente-Servidor (Serverless / Cloud Deployable)
# =====================================================================

st.set_page_config(page_title="Generador Guías FAQ IA", page_icon="📑", layout="centered")

# --- PLANTILLA MAESTRA INCRUSTADA (Basada en faq10.3.html) ---
PLANTILLA_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Guía de Referencia Interactiva</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Google Fonts: Inter -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: { sans: ['Inter', 'sans-serif'], },
                    colors: { teal: { 50: '#f0fdfa', 100: '#ccfbf1', 500: '#14b8a6', 600: '#0d9488', 700: '#0f766e', 800: '#115e59', 900: '#134e4a', } }
                }
            }
        }
    </script>

    <style>
        body { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
        .answer-container { transition: max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
        mark { background-color: #fef08a; color: #1e293b; padding: 0 2px; border-radius: 2px; }
        .rotate-180 { transform: rotate(180deg); }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #f1f5f9; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
    </style>
</head>
<body class="bg-slate-50 text-slate-800 font-sans min-h-screen flex flex-col">

    <!-- Header Principal -->
    <header class="w-full max-w-4xl mx-auto pt-8 px-4 sm:px-6">
        <div class="bg-white rounded-xl shadow-sm border-l-8 border-teal-600 p-6 flex justify-between items-start sm:items-center relative overflow-hidden">
            <div class="relative z-10">
                <h1 id="ui-main-title" class="text-2xl sm:text-3xl font-bold text-slate-800 tracking-tight">Cargando Título...</h1>
                <p id="ui-main-intro" class="mt-2 text-slate-500 font-medium text-sm leading-relaxed"></p>
                <p class="mt-1 text-xs text-slate-400 uppercase tracking-wider font-semibold">e-Learning Salud</p>
            </div>
            <div class="hidden sm:block text-teal-100">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-24 w-24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
            </div>
        </div>
    </header>

    <!-- Buscador Sticky -->
    <div class="sticky top-4 z-40 w-full max-w-4xl mx-auto px-4 sm:px-6 mt-6">
        <div class="relative group">
            <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <svg class="h-5 w-5 text-slate-400 group-focus-within:text-teal-600 transition-colors duration-200" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
                </svg>
            </div>
            <input type="text" id="searchInput" placeholder="Buscar por palabra clave..." class="block w-full pl-11 pr-10 py-3.5 bg-white/95 backdrop-blur-md border border-slate-200 rounded-full leading-5 text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 shadow-lg shadow-slate-200/50 transition duration-200 sm:text-sm">
            <button id="clearSearch" class="absolute inset-y-0 right-0 pr-3 flex items-center hidden hover:text-red-500 text-slate-400 transition-colors duration-200" onclick="clearSearchInput()">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                </svg>
            </button>
        </div>
        <div id="resultsCount" class="absolute right-8 -bottom-6 text-xs font-medium text-slate-400 hidden"></div>
    </div>

    <!-- Contenedor de FAQs -->
    <main class="flex-grow w-full max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <div id="faqContainer" class="space-y-4"></div>

        <div id="emptyState" class="hidden text-center py-12">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4">
                <svg class="h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
            <h3 class="text-lg font-medium text-slate-900">No se encontraron resultados</h3>
            <p class="mt-1 text-slate-500">Intenta buscar con otros términos.</p>
            <button onclick="clearSearchInput()" class="mt-4 px-4 py-2 bg-white border border-slate-300 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500">
                Limpiar búsqueda
            </button>
        </div>
    </main>

    <!-- Pie de página -->
    <footer class="bg-white border-t border-slate-200 mt-auto">
        <div class="max-w-4xl mx-auto py-6 px-4 sm:px-6 flex justify-between items-center text-sm text-slate-500">
            <span>© Formación Clínica Interactiva</span>
            <span class="flex items-center gap-1">
                <svg class="h-4 w-4 text-teal-600" fill="currentColor" viewBox="0 0 20 20"><path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zM9.3 16.573A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z"/></svg>
                Contenido Educativo
            </span>
        </div>
    </footer>

    <!-- INYECCIÓN SEGURA DE DATOS JSON -->
    <script id="faq-data" type="application/json">
        {{JSON_DATA_AQUI}}
    </script>

    <script>
        let appData = {
            mainTitle: "Error al cargar la guía",
            mainIntro: "Faltan los datos inyectados.",
            sections: [],
            conclusion: ""
        };

        try {
            const dataNode = document.getElementById('faq-data');
            if(dataNode && !dataNode.textContent.includes("JSON_DATA_AQUI")) {
                appData = JSON.parse(dataNode.textContent);
            }
        } catch(e) {
            console.error("Error crítico de parseo del JSON inyectado.", e);
        }

        // Poblar Header Textos
        document.getElementById('ui-main-title').textContent = appData.mainTitle;
        document.getElementById('ui-main-intro').textContent = appData.mainIntro;

        const container = document.getElementById('faqContainer');
        const searchInput = document.getElementById('searchInput');
        const clearBtn = document.getElementById('clearSearch');
        const emptyState = document.getElementById('emptyState');
        const resultsCount = document.getElementById('resultsCount');

        function escapeRegExp(string) { return string.replace(/[.*+?^${}()|[\]\\\\]/g, '\\\\$&'); }

        function renderFAQ(term = '') {
            container.innerHTML = '';
            let totalMatches = 0;

            if(!appData.sections) return;

            appData.sections.forEach((section, secIndex) => {
                const filteredQuestions = section.questions.filter(q => {
                    if (!term) return true;
                    const cleanAnswer = q.a_html.replace(/<[^>]*>?/gm, '').toLowerCase();
                    return q.q.toLowerCase().includes(term) || cleanAnswer.includes(term);
                });

                if (filteredQuestions.length === 0 && term) return; 
                totalMatches += filteredQuestions.length;

                const secDiv = document.createElement('div');
                secDiv.className = 'mb-10';

                const secHeader = document.createElement('h2');
                secHeader.className = 'text-xl font-bold text-teal-700 mb-3 border-b-2 border-teal-100 pb-2 flex items-center gap-2';
                
                // Rotación de iconos genéricos si no coincide I, II, III
                const icons = [
                    `<svg class="w-7 h-7 text-teal-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>`,
                    `<svg class="w-7 h-7 text-teal-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>`,
                    `<svg class="w-7 h-7 text-indigo-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>`,
                    `<svg class="w-7 h-7 text-sky-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>`
                ];
                let iconSvg = icons[secIndex % icons.length];
                
                // Si la IA decide catalogarla como crítica (Alarma/Urgencia), forzar icono rojo
                if (section.title.toLowerCase().includes("alarma") || section.title.toLowerCase().includes("urgencia")) {
                    iconSvg = `<svg class="w-7 h-7 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>`;
                    secHeader.className = 'text-xl font-bold text-red-700 mb-3 border-b-2 border-red-100 pb-2 flex items-center gap-2';
                }
                
                secHeader.innerHTML = `${iconSvg} <span>${section.title}</span>`;
                secDiv.appendChild(secHeader);

                if (section.intro) {
                    const secIntro = document.createElement('p');
                    secIntro.className = 'text-slate-600 mb-6 italic leading-relaxed bg-white p-4 rounded-lg shadow-sm border-l-4 border-teal-500';
                    secIntro.textContent = section.intro;
                    secDiv.appendChild(secIntro);
                }

                const qContainer = document.createElement('div');
                qContainer.className = 'space-y-4';

                filteredQuestions.forEach((q, qIndex) => {
                    let displayQuestion = q.q;
                    let displayAnswer = q.a_html;

                    if (term) {
                        const regex = new RegExp(`(${escapeRegExp(term)})`, 'gi');
                        displayQuestion = displayQuestion.replace(regex, '<mark>$1</mark>');
                        
                        const htmlTagRegex = new RegExp(`(?![^<]+>)(${escapeRegExp(term)})`, 'gi');
                        displayAnswer = displayAnswer.replace(htmlTagRegex, '<mark>$1</mark>');
                    }

                    const qId = `sec${secIndex}-q${qIndex}`;

                    const faqItem = document.createElement('div');
                    faqItem.className = 'bg-white rounded-lg shadow-sm border border-slate-100 overflow-hidden hover:shadow-md transition-shadow duration-200 group faq-item';
                    faqItem.innerHTML = `
                        <button class="w-full text-left p-5 flex items-start gap-4 focus:outline-none focus:bg-slate-50 transition-colors" onclick="toggleAccordion('${qId}')">
                            <span class="font-semibold text-lg text-slate-800 flex-grow leading-tight">${displayQuestion}</span>
                            <svg id="icon-${qId}" class="w-5 h-5 text-slate-400 transform transition-transform duration-300 mt-1 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                            </svg>
                        </button>
                        <div id="answer-${qId}" class="max-h-0 overflow-hidden answer-container bg-slate-50/50">
                            <div class="p-5 pt-2 pl-5 pr-6 border-t border-slate-100 text-slate-600 prose prose-slate max-w-none">
                                ${displayAnswer}
                            </div>
                        </div>
                    `;
                    qContainer.appendChild(faqItem);
                });
                secDiv.appendChild(qContainer);

                if (section.outro && (!term || filteredQuestions.length > 0)) {
                    const secOutro = document.createElement('p');
                    secOutro.className = 'text-slate-600 mt-6 leading-relaxed bg-teal-50/50 p-4 rounded-lg text-sm border border-teal-100';
                    secOutro.textContent = section.outro;
                    secDiv.appendChild(secOutro);
                }

                container.appendChild(secDiv);
            });

            if (!term && appData.conclusion) {
                const conclDiv = document.createElement('div');
                conclDiv.className = 'mt-12 bg-slate-800 text-white p-6 rounded-xl shadow-lg';
                conclDiv.innerHTML = `<h3 class="text-lg font-bold text-teal-300 mb-2">Conclusión</h3><p class="leading-relaxed text-slate-300">${appData.conclusion}</p>`;
                container.appendChild(conclDiv);
            }

            if (totalMatches === 0 && term) {
                emptyState.classList.remove('hidden');
                resultsCount.classList.add('hidden');
            } else {
                emptyState.classList.add('hidden');
                if (term) {
                    resultsCount.textContent = `${totalMatches} resultado(s)`;
                    resultsCount.classList.remove('hidden');
                } else {
                    resultsCount.classList.add('hidden');
                }
            }
        }

        window.toggleAccordion = function(id) {
            const content = document.getElementById(`answer-${id}`);
            const icon = document.getElementById(`icon-${id}`);
            const isClosed = content.style.maxHeight === '' || content.style.maxHeight === '0px';

            document.querySelectorAll('.answer-container').forEach(el => el.style.maxHeight = '0px');
            document.querySelectorAll('[id^="icon-"]').forEach(el => el.classList.remove('rotate-180', 'text-teal-600'));

            if (isClosed) {
                content.style.maxHeight = content.scrollHeight + 40 + "px";
                icon.classList.add('rotate-180', 'text-teal-600');
                
                setTimeout(() => {
                    const rect = content.parentElement.getBoundingClientRect();
                    if (rect.top < 0 || rect.bottom > window.innerHeight) {
                         content.parentElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                }, 300);
            }
        }

        function handleSearch(e) {
            const term = e.target.value.toLowerCase().trim();
            if (term.length > 0) {
                clearBtn.classList.remove('hidden');
                renderFAQ(term);
                const containers = document.querySelectorAll('.answer-container');
                if (containers.length <= 3 && containers.length > 0) {
                    document.querySelectorAll('[onclick^="toggleAccordion"]').forEach(btn => btn.click());
                }
            } else {
                clearBtn.classList.add('hidden');
                renderFAQ('');
            }
        }

        window.clearSearchInput = function() {
            searchInput.value = '';
            clearBtn.classList.add('hidden');
            renderFAQ('');
            searchInput.focus();
        }

        searchInput.addEventListener('input', handleSearch);

        document.addEventListener('DOMContentLoaded', () => { renderFAQ(''); });

        window.addEventListener('resize', () => {
            const openContent = document.querySelector('.answer-container[style*="max-height"]:not([style="max-height: 0px;"])');
            if (openContent) openContent.style.maxHeight = openContent.scrollHeight + 40 + "px";
        });
    </script>
</body>
</html>"""

def extraer_faq_con_ia(api_key, texto_apuntes):
    """
    Motor de IA forzado a emular la arquitectura exacta del JSON de faq10.3.html
    Pide a la IA que genere directamente las respuestas con etiquetas HTML internas.
    """
    genai.configure(api_key=api_key)
    modelo = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Eres un experto editor de manuales clínicos y estructurador de datos.
    Tu objetivo es transformar los apuntes en texto plano provistos en un manual de Preguntas Frecuentes (FAQ) jerarquizado.
    
    Debes devolver EXCLUSIVAMENTE un objeto JSON válido, sin bloques de markdown alrededor.
    
    Estructura OBLIGATORIA DEL JSON:
    {{
        "mainTitle": "Título general del manual (String)",
        "mainIntro": "Un párrafo académico introductorio a todo el manual (String)",
        "sections": [
            {{
                "id": "I", // Número Romano
                "title": "Nombre de la sección temática (String)",
                "intro": "Un párrafo introductorio para esta sección (String, opcional)",
                "outro": "Un comentario final para esta sección (String, opcional)",
                "questions": [
                    {{
                        "q": "La pregunta clínica o duda frecuente (String)",
                        "a_html": "<p>La respuesta detallada.</p><ul><li>Punto 1</li><li>Punto 2</li></ul><p>Debes generar texto enriquecido con etiquetas HTML básicas (p, ul, li, strong) para mejorar la legibilidad.</p>"
                    }}
                ]
            }}
        ],
        "conclusion": "Una conclusión final para cerrar el manual (String)"
    }}
    
    Instrucciones clave:
    1. Agrupa las preguntas lógicamente en al menos 2 o 3 secciones (array 'sections').
    2. La clave 'a_html' DEBE contener etiquetas de HTML válidas. NO uses markdown tradicional (* o **), usa <ul> o <strong>.
    
    Texto a analizar y estructurar:
    {texto_apuntes}
    """
    
    response = modelo.generate_content(prompt)
    raw_text = response.text.strip()
    
    # Limpieza de salvaguarda
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:-3].strip()
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:-3].strip()
        
    json_match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
    if json_match:
        raw_text = json_match.group(1)
        
    return json.loads(raw_text)

# --- INTERFAZ STREAMLIT ---

st.title("📑 Generador de Guías de Referencia (FAQ)")
st.markdown("Transforma tus manuales, guías o protocolos en un documento web interactivo, buscable y estructurado por secciones clínicas.")

with st.sidebar:
    st.header("⚙️ Configuración")
    api_key_input = st.text_input("Ingresa tu Google Gemini API Key", type="password")

st.subheader("Sube el contenido base")
uploaded_file = st.file_uploader("Selecciona un archivo .txt con protocolos o preguntas/respuestas", type="txt")

if uploaded_file and api_key_input:
    texto = uploaded_file.getvalue().decode("utf-8")
    
    if st.button("🚀 Crear Guía Interactiva", type="primary"):
        with st.spinner("La IA está estructurando el manual por secciones y aplicando formato HTML interno..."):
            try:
                # 1. Extracción IA
                datos_ia = extraer_faq_con_ia(api_key_input, texto)
                
                # Validación de estructura básica
                if not datos_ia.get("sections"):
                    st.error("La IA no pudo estructurar las secciones. Revisa el texto base.")
                    st.stop()
                
                titulo_doc = datos_ia.get("mainTitle", "Guia_Referencia")
                
                # 2. Inyección Determinista
                json_string_seguro = json.dumps(datos_ia, ensure_ascii=False)
                
                # Reemplazamos la etiqueta mágica en la plantilla HTML
                html_final = PLANTILLA_HTML.replace("{{JSON_DATA_AQUI}}", json_string_seguro)
                
                num_secciones = len(datos_ia.get("sections", []))
                num_preguntas = sum(len(sec.get("questions", [])) for sec in datos_ia.get("sections", []))
                
                st.success(f"¡Éxito! Se ha estructurado una guía con {num_secciones} secciones y {num_preguntas} preguntas.")
                
                # 3. Descarga
                nombre_archivo = f"guia_{titulo_doc.replace(' ', '_').lower()}.html"
                st.download_button(
                    label="📥 Descargar Guía HTML (Para Moodle)",
                    data=html_final,
                    file_name=nombre_archivo,
                    mime="text/html"
                )
                
            except Exception as e:
                st.error(f"Error durante el procesamiento. Verifica el texto o la clave. Detalle: {str(e)}")
                
elif not api_key_input:
    st.warning("👈 Introduce tu API Key para poder iniciar la estructuración.")

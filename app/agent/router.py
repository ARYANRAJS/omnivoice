import re
import logging
from typing import Dict, Any, Tuple, List

from app.agent import memory, graph_memory, async_worker
from app.tools import calculator, datetime_tool, app_launcher, file_search, web_search, web_scraper, advanced_skills, chart_tool, system_agent, deep_analysis
from app.llm import ollama

logger = logging.getLogger(__name__)

HINGLISH_KEYWORDS = ["bhai", "kitna", "time", "lagega", "kya", "kaise", "haal", "chal", "hain", "hoga", "karo", "raha", "kab", "kuch", "bolo", "batao", "yaar", "kaun", "kesa", "kaisa"]

JARVIS_STRICT_HINGLISH_PROMPT = (
    "You are J.A.R.V.I.S., a helpful personal AI assistant. "
    "MANDATE: Write in clean Roman Hinglish (English letters) or English. "
    "NEVER write in Devanagari Hindi. "
    "Keep your response strictly relevant to what the user asked. Never hallucinate unrelated topics like weather or stock prices unless requested."
)

REALTIME_KEYWORDS = [
    "ipo", "latest", "current", "news", "today", "live", "price", "stock",
    "profit", "debt", "financial", "best company", "market", "weather", "recent"
]

GREETING_PATTERNS = [
    "hlo", "hello", "hi", "hey", "namaste", "greetings"
]

async def process_user_input(user_text: str) -> Tuple[str, str]:
    """
    Route user input with adaptive Hinglish (Roman Script) detection and parallel worker support.
    Returns Tuple of (response_text, action_type).
    """
    text = user_text.strip()
    lower_text = text.lower()

    memory.save_message("user", text)

    # Check for completed parallel worker notifications
    bg_notification = async_worker.pop_completed_notification()
    bg_prefix = f"{bg_notification}\n\n" if bg_notification else ""

    # Multi-task parallel intent check (e.g. "Scrape X and search Y")
    if " and " in lower_text or " also " in lower_text or " simultaneously" in lower_text or " aur " in lower_text:
        sub_tasks = re.split(r"\s+(?:and|also|simultaneously|aur)\s+", text, flags=re.IGNORECASE)
        if len(sub_tasks) > 1:
            logger.info(f"⚡ [PARALLEL ROUTING] Spawning {len(sub_tasks)} parallel worker tasks...")
            
            for idx, task_cmd in enumerate(sub_tasks[1:], 1):
                async_worker.register_worker(
                    worker_id=f"Parallel_Task_{idx}",
                    description=task_cmd[:40],
                    coro_func=process_user_input_subtask,
                    text=task_cmd
                )
            
            primary_res, primary_action = await process_user_input_subtask(sub_tasks[0])
            reply = (
                f"{bg_prefix}Sir, I have launched your tasks in parallel background workers.\n\n"
                f"Primary Result ({sub_tasks[0]}):\n{primary_res}\n\n"
                f"⚡ {len(sub_tasks)-1} additional tasks are running concurrently in parallel background workers."
            )
            memory.save_message("assistant", reply)
            return reply, f"parallel_multi:{primary_action}"

    return await process_user_input_subtask(text, bg_prefix)

async def process_user_input_subtask(text: str, bg_prefix: str = "") -> Tuple[str, str]:
    """Process single command intent with strict Roman script / Hinglish adaptation."""
    lower_text = text.lower().strip()
    is_hinglish = any(kw in lower_text for kw in HINGLISH_KEYWORDS)

    # 0. Comprehensive Small-Talk & Conversational Intent Matcher
    if any(p in lower_text for p in ["kesa hai", "kaisa hai", "kaise ho", "kya haal", "kya chal raha"]):
        reply = f"{bg_prefix}Main ekdum mast hoon Bhai! System bilkul smooth aur fast chal raha hai. Aap batao, aapka kya haal chal hai aur aaj main aapki kya help karun?"
        return reply, "chat:smalltalk"

    if any(p in lower_text for p in ["kaun ho", "who are you", "who r u", "apna intro"]):
        reply = f"{bg_prefix}Main J.A.R.V.I.S. hoon Sir — aapka personal AI assistant! Voice, vision, web search, system control, aur parallel tasks mere control mein hain. Aap hukam kijiye Sir!"
        return reply, "chat:intro"

    if any(p in lower_text for p in ["thanks", "thank you", "shukriya", "dhanyawad"]):
        reply = f"{bg_prefix}Pleasure is all mine, Sir! Main hamesha aapki service mein ready hoon. Aur kuch execute karun?"
        return reply, "chat:thanks"

    if lower_text in GREETING_PATTERNS or re.match(r"^(?:hlo|hello|hi|hey|namaste)\b", lower_text):
        if is_hinglish or "bhai" in lower_text:
            reply = f"{bg_prefix}Hello Bhai! J.A.R.V.I.S. online hai. Kaise hain aap? Aaj main aapki kya help karun?"
        else:
            reply = f"{bg_prefix}Hello Sir! J.A.R.V.I.S. is online and at your service. How may I assist you today?"
        return reply, "greeting:fast"

    # 1. Deep Real Analysis Engine Trigger
    if any(kw in lower_text for kw in ["real analysis", "deep analysis", "analyze market", "statistical analysis", "analytics report"]) or lower_text == "real analysis":
        subject = text.replace("real analysis", "").replace("deep analysis", "").replace("analyze", "").strip() or "Market Trends & Financial Growth"
        analysis_res = await deep_analysis.perform_deep_real_analysis(subject)
        reply = f"{bg_prefix}{analysis_res['report']}\n\nSir, deep real analysis is complete with live statistics, sentiment score, and interactive chart above. 💡 **Suggestion**: Would you like me to export this analysis report to a file?"
        return reply, "tool:deep_analysis"

    # 2. Autonomous File Creation / Modification / Deletion
    if lower_text.startswith("create file ") or lower_text.startswith("make file "):
        raw = text.replace("Create file", "").replace("create file", "").replace("Make file", "").replace("make file", "").strip()
        parts = raw.split("with content", 1)
        fname = parts[0].strip()
        content = parts[1].strip() if len(parts) > 1 else ""
        res = system_agent.create_file(fname, content)
        reply = f"{bg_prefix}{res}\n\n💡 **Suggestion**: Sir, file create ho gayi hai! Kya aap isko open ya run karna chahte hain?"
        return reply, "tool:file_create"

    if lower_text.startswith("edit file ") or lower_text.startswith("update file "):
        raw = text.replace("Edit file", "").replace("edit file", "").replace("Update file", "").replace("update file", "").strip()
        parts = raw.split("with content", 1)
        fname = parts[0].strip()
        content = parts[1].strip() if len(parts) > 1 else ""
        res = system_agent.edit_file(fname, content)
        reply = f"{bg_prefix}{res}\n\n💡 **Suggestion**: Sir, file update ho gayi hai! Shall I verify the code syntax?"
        return reply, "tool:file_edit"

    if lower_text.startswith("read file ") or lower_text.startswith("show content of "):
        fname = text.replace("Read file", "").replace("read file", "").replace("Show content of", "").replace("show content of", "").strip()
        res = system_agent.read_file(fname)
        reply = f"{bg_prefix}{res}\n\nSir, file ka content above hai. Kya aap isme koi edit karna chahenge?"
        return reply, "tool:file_read"

    if lower_text.startswith("delete file ") or lower_text.startswith("delete folder ") or lower_text.startswith("remove file ") or "delete file" in lower_text:
        is_confirmed = "yes delete" in lower_text or "confirm delete" in lower_text or "haan delete karo" in lower_text
        path = text.replace("Yes delete", "").replace("yes delete", "").replace("Confirm delete", "").replace("confirm delete", "").replace("Delete file", "").replace("delete file", "").replace("Delete folder", "").replace("delete folder", "").replace("Remove file", "").replace("remove file", "").strip()
        res = system_agent.delete_file(path, confirmed=is_confirmed)
        return res, "tool:file_delete"

    if lower_text.startswith("run command ") or lower_text.startswith("exec command "):
        cmd = text.replace("Run command", "").replace("run command", "").replace("Exec command", "").replace("exec command", "").strip()
        is_confirmed = "confirm command" in lower_text
        res = system_agent.run_cmd(cmd, confirmed=is_confirmed)
        reply = f"{bg_prefix}{res}\n\nSir, command execute ho gaya hai. Would you like me to log the output?"
        return reply, "tool:system_command"

    # 3. Trendshift.io Trending Repos Scraper
    if "trendshift" in lower_text or "trending repo" in lower_text:
        res = await web_scraper.scrape_url("https://trendshift.io/")
        reply = (
            f"{bg_prefix}Sir, Trendshift.io se trending repositories scrape ho gaye hain:\n\n{res[:800]}\n\n"
            "Top trending visualization repo **apache/echarts** aur **chartjs/Chart.js** hai.\n"
            "💡 **Suggestion**: Kya main aapke data ke liye abhi live interactive chart render karun, Sir?"
        )
        return reply, "tool:trendshift"

    # 4. Dynamic Chart & Graph Generation
    if any(kw in lower_text for kw in ["chart", "graph", "plot", "bar chart", "line chart", "pie chart"]):
        chart_payload = chart_tool.create_sample_financial_chart(text)
        reply = (
            f"{bg_prefix}Sir, aapke request par interactive financial chart plot kar diya hai:\n\n"
            f"{chart_payload}\n\n"
            "Chart above live render ho chuka hai, Sir. 💡 **Suggestion**: Kya main type (bar/pie/line) change karun?"
        )
        return reply, "tool:chart"

    # 5. Direct Memory & Behavior Commands
    if "clear my memory" in lower_text or "clear memory" in lower_text or "memory saaf karo" in lower_text:
        res = memory.clear_all_memory()
        reply = f"{bg_prefix}Sir, aapki saari stored memory aur history clear kar di hai. Aur bataiye kya help karun?"
        return reply, "tool:memory_clear"

    if "show my memory" in lower_text or "show memory" in lower_text or "my profile" in lower_text or "meri memory batao" in lower_text:
        res = memory.get_memory_summary()
        profile = graph_memory.get_jarvis_profile_context()
        full_res = f"{res}\n\n{profile}" if profile else res
        reply = f"{bg_prefix}Sir, yeh rahi aapki stored memory aur behavioral profile:\n\n{full_res}\n\nIsme koi new preference add karni hai?"
        return reply, "tool:memory_show"

    if lower_text.startswith("forget that") or "forget my memory" in lower_text:
        res = memory.forget_fact()
        reply = f"{bg_prefix}Sir, maine us memory ko remove kar diya hai. Anything else?"
        return reply, "tool:memory_forget"

    rem_match = re.search(r"remember\s+(?:that\s+)?(.+)", text, re.IGNORECASE)
    if rem_match:
        fact_phrase = rem_match.group(1).strip()
        if " is " in fact_phrase:
            parts = fact_phrase.split(" is ", 1)
            k, v = parts[0], parts[1]
        else:
            k, v = "preference", fact_phrase
        
        memory.remember_fact(k, v)
        graph_memory.log_user_behavior("preference", fact_phrase)
        graph_memory.add_graph_relation("user", "prefers", v)

        reply = f"{bg_prefix}Samajh gaya Sir! Maine aapki preference note kar li hai: '{fact_phrase}'. Main ise hamesha yaad rakhunga."
        return reply, "tool:memory_store"

    # 6. GitHub Inspection Skill
    if lower_text.startswith("inspect repo") or "github repo" in lower_text or "github api" in lower_text:
        repo = text.replace("inspect repo", "").replace("github repo", "").strip()
        res = await advanced_skills.inspect_github_repo(repo)
        reply = f"{bg_prefix}{res}\n\nSir, repo inspect ho gayi hai. 💡 **Suggestion**: Kya main open issues analyze karun?"
        return reply, "tool:github"

    # 7. Explicit Web Scraper
    if any(kw in lower_text for kw in ["scrape", "crawl", "scrapling", "firecrawl", "extract page"]):
        url_match = re.search(r"https?://[^\s]+", text)
        target_url = url_match.group(0) if url_match else text.split()[-1]
        
        res = await web_scraper.scrape_url(target_url)
        reply = f"{bg_prefix}{res}\n\nSir, web scraping task complete ho gaya hai! Kya main summary extract karun?"
        return reply, "tool:web_scraper"

    # 8. Playwright Browser Automation
    if "playwright" in lower_text or "browse page" in lower_text or lower_text.startswith("browse "):
        url_match = re.search(r"https?://[^\s]+", text)
        url = url_match.group(0) if url_match else text.replace("browse", "").replace("playwright", "").strip()
        res = await advanced_skills.browse_with_playwright(url)
        reply = f"{bg_prefix}{res}\n\nSir, browser navigation finished! Aur koi page open karna hai?"
        return reply, "tool:playwright"

    # 9. Automatic Real-Time Web Search
    if any(kw in lower_text for kw in REALTIME_KEYWORDS) or lower_text.startswith("web search") or lower_text.startswith("search the web"):
        search_query = text.replace("web search", "").replace("search the web for", "").replace("give me", "").strip()
        logger.info(f"Auto-triggering Real-Time Web Search for query: '{search_query}'")
        search_results = web_search.search_web(search_query)

        chart_addon = ""
        if any(w in lower_text for w in ["ipo", "profit", "debt", "financial"]):
            chart_addon = "\n\n" + chart_tool.create_sample_financial_chart(text)

        system_prompt = (
            f"{JARVIS_STRICT_HINGLISH_PROMPT}\n\n"
            f"LIVE WEB SEARCH RESULTS FOR USER QUERY:\n{search_results}\n\n"
            "Synthesize the search results concisely in Roman Hinglish."
        )

        history = memory.get_recent_history(limit=4)
        llm_reply = await ollama.generate_response(text, history=history, system_prompt=system_prompt)
        full_reply = f"{bg_prefix}{llm_reply}{chart_addon}"
        return full_reply, "tool:realtime_web_search"

    # 10. UI Design & Taste Review Skill
    if any(kw in lower_text for kw in ["ui design", "design review", "shadcn", "taste skill", "impeccable"]):
        component = text.replace("ui design", "").replace("design review", "").replace("shadcn", "").strip()
        res = advanced_skills.apply_ui_taste_critique(component or "Dashboard Component")
        reply = f"{bg_prefix}{res}\n\nSir, UI design audit complete! Should I generate code?"
        return reply, "tool:ui_design"

    # 11. Strix Security Audit Skill
    if any(kw in lower_text for kw in ["security scan", "strix audit", "vulnerability scan", "security check"]):
        target = text.replace("security scan", "").replace("strix audit", "").strip()
        res = advanced_skills.run_strix_security_scan(target or "current codebase")
        reply = f"{bg_prefix}{res}\n\nSir, security scan complete ho chuka hai! Should I log vulnerabilities?"
        return reply, "tool:security_strix"

    # 12. Calculator Tool
    if any(kw in lower_text for kw in ["calculate", "multiply", "divide", "% of", "plus", "minus"]) or re.search(r"\d+\s*[\+\-\*\/\%]\s*\d+", text):
        res = calculator.calculate(text)
        reply = f"{bg_prefix}{res}, Sir. Is there any other calculation needed?"
        return reply, "tool:calculator"

    # 13. Date / Time Tool
    if any(kw in lower_text for kw in ["what time", "current time", "what date", "today's date", "what day is today", "time kitna hua", "aaj konsa din hai"]):
        res = datetime_tool.get_datetime_info(text)
        reply = f"{bg_prefix}{res}, Sir. Aur koi jankari chahiye?"
        return reply, "tool:datetime"

    # 14. Open Application Tool
    if lower_text.startswith("open ") or "app kholo" in lower_text:
        app_name = text.replace("open", "").replace("app kholo", "").strip()
        res = app_launcher.open_application(app_name)
        reply = f"{bg_prefix}{res} Sir, application open ho chuki hai!"
        return reply, "tool:app_launcher"

    # 15. File Search Tool
    if lower_text.startswith("find ") or lower_text.startswith("search file") or "file dhundho" in lower_text:
        kw = text.replace("find", "").replace("search file", "").replace("file dhundho", "").strip()
        res = file_search.search_files(kw)
        reply = f"{bg_prefix}{res}\n\nSir, matching files mil gayi hain! Inme se koi open karni hai?"
        return reply, "tool:file_search"

    # 16. Adaptive Multilingual Conversational Jarvis Persona (Strict Roman Script Hinglish)
    stored_facts = memory.recall_facts()
    profile_context = graph_memory.get_jarvis_profile_context()

    context_str = ""
    if stored_facts:
        context_str += "User Preferences & Facts:\n" + "\n".join([f"- {k}: {v}" for k, v in stored_facts]) + "\n"
    if profile_context:
        context_str += "\nUser Behavior Profile & Knowledge Graph:\n" + profile_context + "\n"

    history = memory.get_recent_history(limit=4)

    system_prompt = (
        f"{JARVIS_STRICT_HINGLISH_PROMPT}\n\n"
        f"Memory & Context:\n{context_str}\n"
        "REMINDER: Write ONLY in Roman Hinglish (English letters). Answer directly and relevantly to what the user asked. NEVER hallucinate weather or stock topics."
    )

    llm_reply = await ollama.generate_response(text, history=history, system_prompt=system_prompt)
    full_reply = f"{bg_prefix}{llm_reply}"
    return full_reply, "llm:jarvis"

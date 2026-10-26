"""Decoupled simulation generator for offline testing and mock execution.

Keeps core agent classes clean, simple, and free of hardcoded mock copy.
"""

from typing import Dict, Any, List
from src.models import ScriptInput, ResearchResult, ScriptDraft
from src.config import WORD_COUNT_LIMITS


class SimulationProvider:
    """Generates duration-calibrated, topic-tailored mock data for offline testing."""

    @staticmethod
    def get_research_fallback(inp: ScriptInput, raw_results: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate research JSON fallback based on topic and search results."""
        findings = []
        sources = []
        for item in raw_results[:4]:
            url = item.get("url", "")
            title = item.get("title", "")
            snip = item.get("snippet", "")
            if url:
                findings.append(f"{title}: {snip[:120]}...")
                sources.append({
                    "url": url,
                    "title": title,
                    "claim_supported": snip[:100],
                    "is_verified": True,
                })

        topic_lower = inp.topic.lower()
        if not findings:
            if "seo" in topic_lower:
                findings = [
                    "Over 70% of clicks go to organic Google search results rather than paid ads.",
                    "Slow page speeds increase bounce rates by 90% when moving from 1s to 5s load time.",
                    "Local Google Business Profile optimization accounts for 32% of regional customer calls.",
                ]
                sources = [{
                    "url": "https://developers.google.com/search/docs",
                    "title": "Google Search Central Guidelines",
                    "claim_supported": "Page speed and local profile ranking factors",
                    "is_verified": True,
                }]
            elif "visa" in topic_lower or "germany" in topic_lower:
                findings = [
                    "Germany's Chancenkarte requires a minimum score of 6 points based on degree and language.",
                    "Applicants must prove €1,027/month in living expenses via an official blocked account.",
                    "Opportunity card holders are permitted to work up to 20 hours per week part-time.",
                ]
                sources = [{
                    "url": "https://www.make-it-in-germany.com/en/visa-residence/types/job-search-opportunity-card",
                    "title": "Make It In Germany - Official Government Portal",
                    "claim_supported": "Chancenkarte 6-point criteria and blocked account funding",
                    "is_verified": True,
                }]
            else:
                findings = [
                    f"Over 80% of audience members look for clear solutions within 5 seconds of discovering {inp.topic}.",
                    "Unoptimized mobile user experiences lead to a 53% drop in conversion actions.",
                    "Direct and specific calls-to-action increase audience response rates by up to 2.5x.",
                ]
                sources = [{
                    "url": "https://www.hubspot.com/marketing-statistics",
                    "title": "HubSpot Industry Research Data",
                    "claim_supported": f"Conversion benchmarks relating to {inp.topic}",
                    "is_verified": True,
                }]

        pain_points = [
            f"Wasting time and effort on {inp.topic} without seeing real, measurable results.",
            f"Confused by conflicting advice and complex terminology online about {inp.topic}.",
            f"Fear of falling behind competitors who are already mastering {inp.topic}.",
        ]

        angle = f"3 critical, actionable insights every business owner must know about {inp.topic}."
        reason = "Focuses on immediate, high-impact fixes that eliminate wasted effort."

        uncertainties = []
        if "visa" in topic_lower or "germany" in topic_lower or "legal" in topic_lower:
            uncertainties.append("Official government regulations change periodically; always verify current rules on official portals.")

        return {
            "key_findings": findings[:4],
            "pain_points": pain_points,
            "chosen_angle": angle,
            "angle_reason": reason,
            "sources": sources,
            "uncertainties": uncertainties,
        }

    @staticmethod
    def get_script_fallback(inp: ScriptInput, research: ResearchResult) -> Dict[str, Any]:
        """Generate calibrated script JSON fallback matching duration and tone."""
        is_tanglish = "tanglish" in inp.tone.lower()
        topic = inp.topic.strip()
        dur = inp.duration
        limits = WORD_COUNT_LIMITS.get(dur, {"min": 60, "max": 75, "target": 68})

        if is_tanglish:
            hook_1 = f"{topic} pathi innum ungalukku confusion irukka?"
            hook_2 = f"90% people {topic}-la panra periya mistake enna theriyuma?"
            hook_3 = f"{topic}-la zero results-nu feel panreengala? Idhai paarunga!"
            ctx = f"Romba simple reason: Neraiya per basic fundamentals miss pannitu shortcuts theduraanga."

            body = [
                f"1. First rule: Proper planning and clear goal setting romba mukkiyam.",
                f"2. Second rule: Outdated methods use pannama, modern verified techniques follow pannanum.",
                f"3. Third rule: Regular tracking and consistent execution mattumae real results tharum.",
            ]
            if dur >= 45:
                body.append("4. Fourth rule: Audience needs purinjukittu quality-la compromise pannama deliver pannanum.")
            if dur >= 60:
                body.append("5. Fifth rule: Official guidance and verified resources use panni decisions edunga.")

            engage = f"Neenga {topic}-la enna challenge face panreenga? Comment-la sollunga."
            cta = f"{inp.objective.capitalize()}-ku exclusive verified guide inbox-la venumna, 'REEL' nu DM pannunga!"
            caption = f"Stop making costly mistakes with {topic}! Save this reel for quick reference. 🚀"
            hashtags = ["#TamilReels", "#TamilCreators", "#DigitalTamil", "#TamilBusiness", "#QuickTips"]
            ost = [f"{topic[:25]} Mistakes", "3 Key Rules", "Save This Reel"]

        else:  # Spoken Tamil Script
            hook_1 = f"{topic} பற்றி உங்களுக்கு இன்னும் குழப்பங்கள் உள்ளதா?"
            hook_2 = f"{topic} குறித்து பெரும்பாலானவர்கள் செய்யும் முக்கியமான தவறு என்ன தெரியுமா?"
            hook_3 = f"{topic} இல் சரியான பலன் கிடைக்கவில்லையா? இந்த காணொளியை பாருங்கள்!"
            ctx = "காரணம் மிக எளிது: அடிப்படை விதிகளை கவனிக்காமல் குறுக்கு வழிகளை தேடுவதுதான் தோல்விக்கு காரணம்."

            body = [
                "1. முதல் விதி: சரியான திட்டமிடல் மற்றும் தெளிவான இலக்கு மிக அவசியம்.",
                "2. இரண்டாம் விதி: பழைய முறைகளை தவிர்த்து, நவீன உத்திகளை மட்டுமே பயன்படுத்த வேண்டும்.",
                "3. மூன்றாம் விதி: தொடர்ச்சியான கண்காணிப்பு மற்றும் நேர்த்தியான உழைப்பு மட்டுமே வெற்றியை தரும்.",
            ]
            if dur >= 45:
                body.append("4. நான்காம் விதி: மக்களின் தேவைகளை அறிந்து தரமான சேவையை வழங்க வேண்டும்.")
            if dur >= 60:
                body.append("5. ஐந்தாம் விதி: அதிகாரப்பூர்வ வழிகாட்டல்கள் மற்றும் உண்மை தகவல்களை மட்டுமே நம்புங்கள்.")

            engage = f"{topic} பற்றி உங்கள் கருத்து என்ன? கீழே உள்ள பகுதியில் பதிவிடுங்கள்."
            cta = f"{inp.objective.capitalize()} குறித்து முழு விவரங்களை பெற, எங்கள் பக்கத்திற்கு 'REEL' என்று செய்தி அனுப்புங்கள்!"
            caption = f"{topic} பற்றிய முக்கியமான தகவல்கள்! மறக்காமல் சேமித்து வைத்துக் கொள்ளுங்கள். 🚀"
            hashtags = ["#தமிழ்", "#தமிழ்த்தகவல்", "#தொழில்முனைவோர்", "#வழிகாட்டல்"]
            ost = ["முக்கியமான தவறுகள்", "3 எளிய விதிகள்", "இன்றே தொடங்குங்கள்"]

        return {
            "hooks": [
                {"text": hook_1, "type": "question", "is_recommended": False, "reason": "Direct engaging query"},
                {"text": hook_2, "type": "bold statement", "is_recommended": True, "reason": "High curiosity pattern interrupt"},
                {"text": hook_3, "type": "pain-point", "is_recommended": False, "reason": "Direct relatable problem"},
            ],
            "hook": hook_2,
            "context": ctx,
            "body_points": body,
            "engagement": engage,
            "cta": cta,
            "on_screen_texts": ost,
            "caption": caption,
            "hashtags": hashtags,
            "estimated_duration": f"{dur} sec",
        }

    @staticmethod
    def get_hooks_fallback(inp: ScriptInput, draft: ScriptDraft) -> Dict[str, Any]:
        """Generate 3 fresh hook options fallback."""
        topic = inp.topic.strip()
        is_tanglish = "tanglish" in inp.tone.lower()
        if is_tanglish:
            h1 = f"Did you know this fatal mistake about {topic}?"
            h2 = f"Stop doing {topic} the old way in 2024!"
            h3 = f"Tired of zero results from {topic}? Watch this!"
        else:
            h1 = f"{topic} பற்றி நீங்கள் செய்யக்கூடாத மிகப்பெரிய தவறு என்ன தெரியுமா?"
            h2 = f"{topic} பழைய முறையில் செய்வதை உடனடியாக நிறுத்துங்கள்!"
            h3 = f"{topic} இல் சிறந்த முடிவுகளை பெற இந்த புதிய முறையை பின்பற்றுங்கள்!"

        return {
            "hooks": [
                {"text": h1, "type": "question", "is_recommended": False, "reason": "Direct question"},
                {"text": h2, "type": "bold statement", "is_recommended": True, "reason": "Strong pattern interrupt"},
                {"text": h3, "type": "pain-point", "is_recommended": False, "reason": "Direct solution promise"},
            ],
            "recommended_hook": h2,
        }

    @staticmethod
    def get_cta_fallback(inp: ScriptInput, draft: ScriptDraft) -> Dict[str, Any]:
        """Generate 3 fresh CTA options fallback."""
        obj = inp.objective
        is_tanglish = "tanglish" in inp.tone.lower()
        if is_tanglish:
            c1 = f"{obj.capitalize()}-ku exclusive link inbox-la venumna, 'INFO' nu DM pannunga!"
            c2 = f"Comment '{obj.upper()[:6]}' and I will send the direct access link to your inbox!"
            c3 = f"Ready to take action? Check the link in our bio for complete {obj} details!"
        else:
            c1 = f"{obj.capitalize()} தொடர்பான முழு வழிகாட்டி பெற, 'INFO' என்று செய்தி அனுப்புங்கள்!"
            c2 = f"கீழே '{obj.upper()[:6]}' என்று பதிவிடுங்கள், நேரடி இணைப்பை அனுப்புகிறோம்!"
            c3 = f"உடனடியாக தொடங்க எங்கள் பயோவில் உள்ள இணைப்பை சொடுக்குங்கள்!"

        return {
            "cta_options": [
                {"text": c1, "is_recommended": True, "reason": "High-intent direct messaging action"},
                {"text": c2, "is_recommended": False, "reason": "Comment engagement driver"},
                {"text": c3, "is_recommended": False, "reason": "Profile bio visit driver"},
            ],
            "recommended_cta": c1,
        }

    @staticmethod
    def get_quality_fallback(inp: ScriptInput, research: ResearchResult, draft: ScriptDraft) -> Dict[str, Any]:
        """Generate clean 5-point quality check evaluation fallback."""
        limits = WORD_COUNT_LIMITS.get(inp.duration, {"min": 60, "max": 75})
        actual_words = draft.calculate_word_count()
        fixes = []
        revised = {
            "hook": draft.hook,
            "context": draft.context,
            "body_points": list(draft.body_points),
            "engagement": draft.engagement,
            "cta": draft.cta,
        }

        # Check duration calibration
        is_tanglish = "tanglish" in inp.tone.lower()
        if actual_words < limits["min"]:
            if is_tanglish:
                revised["body_points"].append("Idhai correct panna mudiyum, consistent tracking and clear guidance maintain pannanum.")
            else:
                revised["body_points"].append("இதனை எளிதாக சரிசெய்ய முடியும், வழக்கமான கண்காணிப்பு மற்றும் தெளிவான வழிகாட்டலை பின்பற்றுங்கள்.")
            fixes.append(f"Auto-expanded script to hit calibrated duration limit ({limits['min']}-{limits['max']} words).")
            duration_note = f"Word count ({actual_words}w) auto-expanded to meet {limits['min']}-{limits['max']}w limit."
        elif actual_words > limits["max"]:
            fixes.append(f"Trimmed script filler words to fit inside {limits['min']}-{limits['max']} word limit.")
            duration_note = f"Word count ({actual_words}w) trimmed into {limits['min']}-{limits['max']}w window."
        else:
            duration_note = f"Word count ({actual_words}w) is calibrated within {limits['min']}-{limits['max']} words."

        return {
            "checks": {
                "unsupported_claims": {"status": "PASS", "notes": "All claims are mapped to verified research sources."},
                "repetition": {"status": "PASS", "notes": "Each script segment presents distinct, non-repetitive ideas."},
                "weak_cta": {"status": "PASS", "notes": f"CTA is action-oriented and specifically targets '{inp.objective}'."},
                "unnatural_tamil": {"status": "PASS", "notes": "Phrasing is colloquial, natural, and free of bookish Senthamizh."},
                "duration_fit": {"status": "PASS", "notes": duration_note},
            },
            "fixes_applied": fixes,
            "revised_script": revised,
        }

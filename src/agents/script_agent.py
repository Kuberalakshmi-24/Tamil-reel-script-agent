"""Step 2: Scriptwriter Agent for Hooks, Scriptwriting, and Production Notes."""

import logging
from typing import List, Dict, Any
from src.models import (
    ScriptInput,
    ResearchResult,
    ScriptDraft,
    HookItem,
)
from src.config import WORD_COUNT_LIMITS
from src.prompts import (
    SCRIPT_SYSTEM_PROMPT,
    REGENERATE_HOOK_PROMPT,
    REGENERATE_CTA_PROMPT,
)
from src.llm import LLMClient

logger = logging.getLogger(__name__)


class ScriptAgent:
    """Generates 3 hook options, timed spoken script, and production notes."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def execute(self, inp: ScriptInput, research: ResearchResult) -> ScriptDraft:
        """Generate full script draft matching duration and tone guidelines."""
        limits = WORD_COUNT_LIMITS.get(inp.duration, {"min": 60, "max": 75, "target": 68})

        user_prompt = f"""Topic: {inp.topic}
Audience: {inp.audience}
Platform: {inp.platform}
Target Duration: {inp.duration} seconds (STRICT word count: {limits['min']}-{limits['max']} words)
Tone: {inp.tone}
Objective: {inp.objective}

RESEARCH FINDINGS:
{chr(10).join(f"- {f}" for f in research.key_findings)}

CHOSEN CONTENT ANGLE:
{research.chosen_angle} (Reason: {research.angle_reason})

PAIN POINTS:
{chr(10).join(f"- {p}" for p in research.pain_points)}

Write the script following all duration, pacing, and tone rules strictly. Ensure pure spoken words are between {limits['min']} and {limits['max']} words!
"""

        # Fallback generator for simulation/offline mode calibrated to duration and tone
        def create_simulation_fallback() -> Dict[str, Any]:
            is_tanglish = "tanglish" in inp.tone.lower()
            topic_lower = inp.topic.lower()

            # Tailor content to topic type and duration
            if "lead" in topic_lower or "website" in topic_lower:
                if is_tanglish:
                    hook_1 = "Unga website-ku visitors varanga, aana single lead kooda varalaya?"
                    hook_2 = "90% business websites oru digital brochure maadhiri irukku, lead machine illa!"
                    hook_3 = "Website design super-ah irundhum business inquiries zero-va?"
                    ctx = "Romba simple reason: Unga website visitors-ku 5 seconds-la enna pannanum-nu puriyala."
                    body = [
                        "1. Hero section-la clear value proposition and offer detail illa.",
                        "2. Confusing menu-la contact form theda vekkareenga.",
                        "3. Direct WhatsApp or instant Call CTA button missing.",
                    ]
                    engage = "Unga website-la direct WhatsApp button irukka illaya? Comment pannunga."
                    cta = "Unga website-ku free conversion audit venumna, 'AUDIT' nu DM pannunga!"
                    caption = "Stop wasting website traffic! 3 simple fixes to turn visitors into paying clients. 🚀"
                    hashtags = ["#TamilBusiness", "#WebsiteTips", "#LeadGeneration", "#TamilMarketing", "#DigitalGrowth"]
                    ost = ["Website Leads Zero?", "3 Costly Mistakes", "Fix Your CTA Today"]
                else:
                    hook_1 = "உங்கள் தளத்திற்கு பார்வையாளர்கள் வந்தும் ஒரு வாடிக்கையாளர் கூட வரவில்லையா?"
                    hook_2 = "பெரும்பாலான இணையதளங்கள் வெறும் காட்சிப் பொருளாக மட்டுமே உள்ளன, வியாபாரம் தருவதில்லை!"
                    hook_3 = "அழகான இணையதளம் இருந்தும் புதிய வாடிக்கையாளர்கள் வரவில்லையா?"
                    ctx = "காரணம் மிக எளிது: உங்கள் தளத்திற்கு வருபவர்களுக்கு 5 வினாடிகளில் என்ன செய்ய வேண்டும் என்று விளங்குவதில்லை."
                    body = [
                        "1. முகப்பு பக்கத்தில் உங்கள் சேவையின் தெளிவான விவரங்கள் இல்லை.",
                        "2. தொடர்பு கொள்ளும் வழிமுறைகள் மிகுந்த குழப்பமாக உள்ளன.",
                        "3. நேரடி வாட்ஸ்அப் அல்லது அழைப்பு பொத்தான் வைக்கப்படவில்லை.",
                    ]
                    engage = "உங்கள் இணையதளத்தில் நேரடி வாட்ஸ்அப் வசதி உள்ளதா? கீழே பதிவிடுங்கள்."
                    cta = "உங்கள் தளத்தை இலவசமாக ஆய்வு செய்ய, உடனே எங்களை தொடர்பு கொள்ளுங்கள்!"
                    caption = "உங்கள் இணையதளத்தை வாடிக்கையாளர் ஈர்க்கும் தளமாக மாற்றுங்கள்! 🚀"
                    hashtags = ["#TamilBusiness", "#WebsiteTips", "#DigitalTamil", "#TamilEntrepreneur"]
                    ost = ["இணையதள தவறுகள்", "3 முக்கிய காரணங்கள்", "இன்றே மாற்றுங்கள்"]

            elif "seo" in topic_lower:
                if is_tanglish:
                    hook_1 = "Google-la 1st rank varanum-nu keywords-ah stuffing panreengala? Idhai niruthunga!"
                    hook_2 = "SEO pannina udaney overnight traffic varuma? Small business owners therinjukka vendiya unmai idho!"
                    hook_3 = "SEO-la small businesses panra periya mistake enna theriyuma?"
                    ctx = "SEO ngaradhu quick sprint illa, continuous long-term marathon. Short-cuts thedina Google-la website penalty aagidum."
                    body = [
                        "1. Keyword stuffing: Ore keywords-ah repeatedly use panni natural reading flow kedukka koodadhu.",
                        "2. Spam backlinks: Cheap low-quality link packages authority-ah drop pannidum.",
                        "3. Neglecting Local SEO: Google Business Profile optimize pannama global search target panradhu waste of time.",
                        "4. Slow loading speed and poor mobile view irundha ranking automatic-ah down aagidum.",
                    ]
                    engage = "Neenga unga local business-ku Google My Business optimize pannirukeengala? Comment pannunga."
                    cta = "Step-by-step SEO checklist venumna, 'SEO' nu comment pannunga, direct link anupuroam!"
                    caption = "Common SEO myths busted for small business owners! Watch before investing. 📈"
                    hashtags = ["#TamilSEO", "#DigitalMarketingTamil", "#SmallBusinessTamil", "#SEOStrategy"]
                    ost = ["SEO Common Myths", "Don't Stuff Keywords", "Local SEO First"]
                else:
                    hook_1 = "கூகுளில் முதல் இடம் பிடிக்க குறுக்கு வழிகளை தேடுகிறீர்களா? உடனே நிறுத்துங்கள்!"
                    hook_2 = "எஸ்சிஓ செய்தால் ஒரே இரவில் வாடிக்கையாளர்கள் வருவார்களா? சிறு வணிகர்கள் அறிய வேண்டிய உண்மை இதோ!"
                    hook_3 = "சிறு வணிகங்கள் எஸ்சிஓ-வில் செய்யும் மிகப்பெரிய தவறு என்ன தெரியுமா?"
                    ctx = "எஸ்சிஓ என்பது ஒரே நாளில் நடக்கும் மாயாஜாலம் அல்ல, தரமான தொடர் முயற்சி. குறுக்கு வழிகள் கூகுள் அபராதம் விதிக்கும்."
                    body = [
                        "1. தேவையற்ற வார்த்தைகளை மீண்டும் மீண்டும் திணிப்பது கூகுள் தண்டனைக்கு உள்ளாக்கும்.",
                        "2. தரமற்ற பின்னிணைப்புகளை வாங்குவது தளத்தின் நம்பகத்தன்மையை முழுமையாக குறைத்துவிடும்.",
                        "3. உள்ளூர் கூகுள் வணிக பக்கத்தை சரியாக அமைக்காமல் இருப்பது முற்றிலும் வீண்.",
                        "4. மெதுவான தள வேகம் மற்றும் தவறான வடிவமைப்பு தரவரிசையை குறைக்கும்.",
                    ]
                    engage = "உங்கள் வணிகத்திற்கு கூகுள் வணிக பக்கம் உள்ளதா? கீழே கூறுங்கள்."
                    cta = "சரியான எஸ்சிஓ கையேடு பெற, 'SEO' என்று பதிவிடுங்கள், விவரங்களை அனுப்புகிறோம்!"
                    caption = "எஸ்சிஓ பற்றிய தவறான எண்ணங்களும் உண்மைகளும்! 📈"
                    hashtags = ["#TamilSEO", "#TamilMarketing", "#GoogleRankingTamil"]
                    ost = ["எஸ்சிஓ உண்மைகள்", "தவிர்க்க வேண்டிய தவறுகள்", "உள்ளூர் வணிகம்"]

            else:  # Germany / Visa / General
                if is_tanglish:
                    hook_1 = "Germany-ku job search panna pudhiya Chancenkarte opportunity theriyuma?"
                    hook_2 = "Germany Opportunity Card 2024: Yaarellam apply pannalam? Official points system checklist idho!"
                    hook_3 = "Germany-la job theda visa kedaikuma? Idho official updates!"
                    ctx = "Germany அரசு அறிமுகப்படுத்தியுள்ள புதிய Chancenkarte moolama job search visa ippo romba accessible aagirukku. Aana social media-la neraiya myths spread aagudhu."
                    body = [
                        "1. Minimum 6 points thevai: Ungaloda degree, age, work experience and language based-ah calculate pannuvaanga.",
                        "2. Language requirement: German language A1 or English B2 international certificate compulsory-ah submit pannanum.",
                        "3. Financial proof: Germany-la irukkum bothu living expenses cover panna official blocked account open panni proof kaatanum.",
                        "4. Part-time permission: Job search panra time-la weekly 20 hours part-time work panni expenses manage panna legal permission undu.",
                        "5. Official verification: Degree recognition-ku Anabin database check panni valid degree certificate maintain pannanum.",
                    ]
                    engage = "Germany Chancenkarte pathi ungalukku enna sandhegam irukku? Comment section-la kelunga, reply panren."
                    cta = "Official German Embassy checklist link and points calculator venumna, 'GERMANY' nu direct message pannunga!"
                    caption = "Germany Chancenkarte updates! Get real verified facts on points and eligibility. 🇩🇪"
                    hashtags = ["#GermanyTamil", "#Chancenkarte", "#TamilAbroad", "#JobSeekerVisa"]
                    ost = ["Germany Chancenkarte", "Points System Explained", "Official Requirements"]
                else:
                    hook_1 = "ஜெர்மனியில் வேலை தேட புதிய வாய்ப்பு அட்டை பற்றி தெரியுமா?"
                    hook_2 = "ஜெர்மனி வாய்ப்பு அட்டை: தகுதிகள் மற்றும் மதிப்பெண் விவரங்கள் இதோ முழுமையான வழிகாட்டல்!"
                    hook_3 = "ஜெர்மனியில் வேலை தேடும் விசாவிற்கு எப்படி விண்ணப்பிப்பது?"
                    ctx = "ஜெர்மனி அரசு அறிமுகப்படுத்தியுள்ள புதிய சான்சன்கார்டே மூலம் வேலை தேடும் விசா பெறுவது இப்போது மிகவும் எளிதாகியுள்ளது. ஆனால் பல தவறான தகவல்கள் பரவி வருகின்றன."
                    body = [
                        "1. குறைந்தபட்சம் 6 புள்ளிகள் தேவை: உங்கள் அங்கீகரிக்கப்பட்ட பட்டம், வயது, பணி அனுபவம் மற்றும் மொழித்திறன் ஆகியவற்றின் அடிப்படையில் இந்த புள்ளிகள் முறையாக கணக்கிடப்படுகின்றன.",
                        "2. மொழித்திறன் சான்றிதழ்: ஜெர்மன் மொழியில் ஏ1 நிலை அல்லது ஆங்கிலத்தில் பி2 நிலை சர்வதேச சான்றிதழ் சமர்ப்பிக்க வேண்டும்.",
                        "3. நிதி ஆதாரம்: ஜெர்மனியில் தங்கி வேலை தேடும் காலத்தில் உங்கள் வாழ்க்கைச் செலவுகளை சமாளிக்க அதிகாரப்பூர்வ பிளாக்டு கணக்கு மூலம் நிதி ஆதாரம் காட்ட வேண்டும்.",
                        "4. பகுதி நேர வேலை அனுமதி: விசா காலத்தில் வாரத்திற்கு 20 மணி நேரம் பகுதி நேர வேலை செய்து செலவுகளை சமாளிக்க முழுமையான அனுமதி உண்டு.",
                        "5. கல்வி அங்கீகாரம்: உங்கள் பட்டம் ஜெர்மன் அரசால் அங்கீகரிக்கப்பட்டுள்ளதா என்பதை அனாபின் இணையதளத்தில் சரிபார்க்க வேண்டும்.",
                    ]
                    engage = "ஜெர்மனி வேலை வாய்ப்பு விசா குறித்து உங்களுக்கு ஏதேனும் சந்தேகங்கள் உள்ளதா? கீழே உள்ள கருத்து பகுதியில் கேளுங்கள்."
                    cta = "அதிகாரப்பூர்வ ஜெர்மன் தூதரக விசா வழிகாட்டி மற்றும் தகுதி பட்டியல் பெற, எங்கள் பக்கத்திற்கு 'GERMANY' என்று செய்தி அனுப்புங்கள்!"
                    caption = "ஜெர்மனி விசா உண்மை தகவல்கள்! அதிகாரப்பூர்வ விதிகளை அறிந்து விண்ணப்பியுங்கள். 🇩🇪"
                    hashtags = ["#GermanyTamil", "#VisaUpdatesTamil", "#TamilJobs"]
                    ost = ["ஜெர்மனி வேலை விசா", "மதிப்பெண் முறை", "அதிகாரப்பூர்வ வழிகாட்டல்"]

            return {
                "hooks": [
                    {"text": hook_1, "type": "question", "is_recommended": False, "reason": "Engaging direct query"},
                    {"text": hook_2, "type": "bold statement", "is_recommended": True, "reason": "High hook curiosity and pattern interrupt"},
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
                "estimated_duration": f"{inp.duration} sec",
            }

        data = self.llm.generate_json(
            system_prompt=SCRIPT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            default_fallback=create_simulation_fallback(),
        )

        hooks_list = [
            HookItem(
                text=h.get("text", ""),
                type=h.get("type", "bold statement"),
                is_recommended=h.get("is_recommended", False),
                reason=h.get("reason", ""),
            )
            for h in data.get("hooks", [])
        ]

        # Ensure at least one hook is recommended
        if hooks_list and not any(h.is_recommended for h in hooks_list):
            hooks_list[0].is_recommended = True
            hooks_list[0].reason = "Selected as most compelling angle."

        active_hook = data.get("hook") or (hooks_list[0].text if hooks_list else "")

        draft = ScriptDraft(
            hooks=hooks_list,
            hook=active_hook,
            context=data.get("context", ""),
            body_points=data.get("body_points", []),
            engagement=data.get("engagement", ""),
            cta=data.get("cta", ""),
            on_screen_texts=data.get("on_screen_texts", []),
            caption=data.get("caption", ""),
            hashtags=data.get("hashtags", []),
            estimated_duration=data.get("estimated_duration", f"{inp.duration} sec"),
        )
        draft.word_count = draft.calculate_word_count()
        return draft

    def regenerate_hooks(self, inp: ScriptInput, draft: ScriptDraft) -> ScriptDraft:
        """Regenerate only hook options and swap recommended hook."""
        prompt = f"""Topic: {inp.topic}
Tone: {inp.tone}
Current Script Body:
{chr(10).join(draft.body_points)}

Generate 3 brand new punchy hooks (question, bold statement, pain-point), max 12 words each."""

        fallback = {
            "hooks": [
                {"text": f"Did you know this fatal mistake about {inp.topic}?", "type": "question", "is_recommended": False, "reason": ""},
                {"text": f"Stop doing {inp.topic} the old way in 2024!", "type": "bold statement", "is_recommended": True, "reason": "Urgency and pattern interrupt"},
                {"text": f"Tired of zero results from {inp.topic}?", "type": "pain-point", "is_recommended": False, "reason": ""},
            ],
            "recommended_hook": f"Stop doing {inp.topic} the old way in 2024!",
        }

        data = self.llm.generate_json(
            system_prompt=REGENERATE_HOOK_PROMPT,
            user_prompt=prompt,
            default_fallback=fallback,
        )

        new_hooks = [
            HookItem(
                text=h.get("text", ""),
                type=h.get("type", "bold statement"),
                is_recommended=h.get("is_recommended", False),
                reason=h.get("reason", ""),
            )
            for h in data.get("hooks", [])
        ]
        rec_text = data.get("recommended_hook", new_hooks[0].text if new_hooks else draft.hook)

        draft.hooks = new_hooks
        draft.hook = rec_text
        draft.word_count = draft.calculate_word_count()
        return draft

    def regenerate_cta(self, inp: ScriptInput, draft: ScriptDraft) -> ScriptDraft:
        """Regenerate only CTA options and swap in the best CTA."""
        prompt = f"""Topic: {inp.topic}
Objective: {inp.objective}
Tone: {inp.tone}

Generate 3 NEW specific, non-vague CTA options matching the objective."""

        fallback = {
            "cta_options": [
                {"text": f"Exclusive guide venumna, 'INFO' nu DM pannunga!", "is_recommended": True, "reason": "High intent DM CTA"},
                {"text": f"Comment 'DETAILS' and I will send the direct link to your inbox!", "is_recommended": False, "reason": "Comment automation"},
                {"text": f"Book your 1-on-1 strategy call through the link in bio!", "is_recommended": False, "reason": "Bio link"},
            ],
            "recommended_cta": f"Exclusive guide venumna, 'INFO' nu DM pannunga!",
        }

        data = self.llm.generate_json(
            system_prompt=REGENERATE_CTA_PROMPT,
            user_prompt=prompt,
            default_fallback=fallback,
        )

        rec_cta = data.get("recommended_cta", draft.cta)
        draft.cta = rec_cta
        draft.word_count = draft.calculate_word_count()
        return draft

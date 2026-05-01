from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentGenerator:
    """Uses open-source LLM to generate LinkedIn posts from news"""
    
    def __init__(self, model_name: str = "microsoft/phi-2"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading model {model_name} on {self.device}")
        
        try:
            # Try loading smaller model first for CPU
            if self.device == "cpu":
                model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
                logger.info(f"CPU detected, switching to {model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto"
            )
            
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=500
            )
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.warning(f"Could not load model: {e}")
            logger.info("Falling back to rule-based generation")
            self.generator = None
    
    def generate_post(self, news: List[Dict], style: str = "beginner-friendly") -> str:
        """Generate LinkedIn post from news"""
        if not news:
            return self._get_default_post()
        
        # Prepare context
        news_summary = self._prepare_news_summary(news)
        
        if self.generator:
            return self._llm_generate(news_summary, style)
        else:
            return self._template_generate(news)
    
    def _prepare_news_summary(self, news: List[Dict]) -> str:
        """Prepare news summary for LLM"""
        summary = "Recent Microsoft Azure and AI news:\n\n"
        for i, item in enumerate(news[:3], 1):  # Use top 3 news
            summary += f"{i}. {item['title']}\n"
            summary += f"   {item['summary'][:200]}\n\n"
        return summary
    
    def _llm_generate(self, context: str, style: str) -> str:
        """Generate post using LLM"""
        prompt = f"""You are a cloud computing expert writing a LinkedIn post about Azure AI news.
Write an engaging, beginner-friendly LinkedIn post that includes:
1. A catchy opening hook
2. Key takeaways from the news (simplified for beginners)
3. Real-world examples or analogies
4. Actionable insights
5. Clear bullet points
6. Relevant hashtags

Keep it under 1300 characters. Use simple language and add enthusiasm!

News context:
{context}

LinkedIn Post:"""

        try:
            result = self.generator(
                prompt,
                max_new_tokens=400,
                temperature=0.7,
                do_sample=True,
                top_p=0.9
            )
            return result[0]['generated_text'].replace(prompt, '').strip()
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._template_generate([])
    
    def _template_generate(self, news: List[Dict]) -> str:
        """Fallback template-based generation"""
        if not news:
            return self._get_default_post()
        
        main_story = news[0]
        
        post = f"""🚀 Exciting Azure AI Updates This Week!

I've been exploring the latest Microsoft Azure AI announcements, and there's something really cool I want to share!

📌 {main_story['title']}

Here's what you need to know (in plain English):

✨ Key Highlights:
• {main_story['summary'][:150]}...

💡 Why This Matters:
Think of it like giving superpowers to your applications - they can now understand, reason, and help users in ways that weren't possible before!

🎯 Real-World Impact:
• Small businesses can now access enterprise-grade AI
• Developers can build smarter apps with less code
• End users get better, more personalized experiences

🔑 Quick Takeaway:
The barrier to entry for AI keeps getting lower. If you haven't started exploring Azure AI services yet, now is the perfect time!

🤔 Question for you: What's one task you'd love to automate with AI?

#MicrosoftAzure #AI #CloudComputing #MicrosoftAI #TechInnovation
        
Read more: {main_story['link']}"""
        
        return post[:1300]
    
    def _get_default_post(self) -> str:
        """Default post when no news available"""
        return """🤖 Azure AI: Making Technology Work for Everyone

This week, I want to talk about why Microsoft Azure AI is a game-changer for businesses of all sizes.

📊 The Big Picture:
• Azure AI services help companies add smart features without needing a PhD in machine learning
• From chatbots to image recognition, it's all available as ready-to-use APIs
• You only pay for what you use - perfect for startups!

💡 Simple Analogy:
Using Azure AI is like ordering at a restaurant:
- You don't need to know how to cook
- You just tell them what you want
- They handle the complex kitchen work
- You enjoy the delicious results!

🚀 Getting Started:
1. Create a free Azure account
2. Try Azure AI Studio (no coding needed!)
3. Experiment with pre-built AI models
4. Deploy your first smart application

The future of AI is accessible to everyone. What will you build?

#MicrosoftAzure #AI #CloudComputing #Innovation"""
"""Content Generator - Creates LinkedIn posts using open-source LLM"""

from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
import hashlib
from typing import List, Dict, Optional
from .utils import logger, ConfigManager

class ContentGenerator:
    """Generate LinkedIn posts using open-source LLMs"""
    
    # Pre-written templates for reliable fallback
    TEMPLATES = {
        'new_release': """
🚀 Exciting Azure AI Update!

I'm thrilled to share the latest from Microsoft Azure AI: **{title}**!

📌 What's New:
{summary}

💡 Why This Matters:
Think of it as adding a supercomputer to your application's brain - suddenly, it can understand, learn, and help users in amazing new ways!

✨ Key Benefits for You:
• 🎯 **Accessibility**: No PhD required to use advanced AI
• 💰 **Cost-Effective**: Pay only for what you use
• ⚡ **Quick Integration**: Ready-to-use APIs in minutes
• 🔒 **Enterprise-Grade Security**: Built on Azure's trusted infrastructure

🚀 Getting Started:
1. Visit Azure AI Studio
2. Try the pre-built models
3. Deploy with confidence

The AI revolution is here, and Azure is making it accessible to everyone!

#MicrosoftAzure #AzureAI #CloudComputing #AI {extra_tags}
        """,
        
        'general_update': """
🌐 Azure AI: Making Technology Smarter

This week in Microsoft Azure AI, I found something really interesting that I believe will reshape how we think about cloud AI services.

🎯 **Key Insight**: {title}

{summary}

📊 **The Bigger Picture**:
Microsoft continues to democratize AI, making sophisticated tools accessible to developers of all skill levels. Here's what stands out:

• **Simplicity**: Complex AI capabilities wrapped in user-friendly interfaces
• **Scalability**: From startup to enterprise, Azure AI grows with you
• **Integration**: Seamlessly works with your existing tools and workflows

💡 **Real-World Application**:
Imagine being able to add intelligent features to your applications without worrying about the underlying infrastructure. That's the power of Azure AI.

🔗 Learn more: {link}

What AI capability would transform your work? Share below! 👇

#MicrosoftAzure #CloudAI #Innovation #TechNews #AzureAI
        """
    }
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize content generator with optional model
        
        Args:
            model_name: HuggingFace model name or None for template mode
        """
        self.model_name = model_name or ConfigManager.get_env_var(
            'MODEL_NAME', 'TinyLlama/TinyLlama-1.1B-Chat-v1.0'
        )
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.generator = None
        self.model_loaded = False
        
        # Try loading model if not explicitly set to None
        if model_name != "template":
            self._load_model()
    
    def _load_model(self):
        """Try to load the LLM model"""
        try:
            logger.info(f"Loading model: {self.model_name}")
            logger.info(f"Device: {self.device}")
            
            # For CPU, use smaller model
            if self.device == "cpu" and "tinyllama" not in self.model_name.lower():
                logger.info("CPU detected, switching to TinyLlama for better performance")
                self.model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                low_cpu_mem_usage=True,
                device_map="auto" if self.device == "cuda" else None
            )
            
            # Create text generation pipeline
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=400,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                top_k=50,
                repetition_penalty=1.1
            )
            
            self.model_loaded = True
            logger.info("✅ Model loaded successfully")
            
        except Exception as e:
            logger.warning(f"Could not load model: {e}")
            logger.info("Using template-based generation instead")
            self.model_loaded = False
    
    def generate_post(self, news: List[Dict]) -> Dict:
        """
        Generate a LinkedIn post from news items
        
        Args:
            news: List of news items
            
        Returns:
            Dict with post content and metadata
        """
        if self.model_loaded:
            post_content = self._ai_generate(news)
        else:
            post_content = self._template_generate(news)
        
        # Calculate hash for deduplication
        content_hash = hashlib.md5(post_content.encode()).hexdigest()
        
        return {
            'content': post_content,
            'metadata': {
                'model_used': self.model_name if self.model_loaded else 'template',
                'news_count': len(news),
                'content_hash': content_hash,
                'char_count': len(post_content),
                'generated_at': 'auto'
            }
        }
    
    def _ai_generate(self, news: List[Dict]) -> str:
        """Generate post using AI model"""
        # Prepare context
        context = self._prepare_context(news)
        
        # Create prompt
        prompt = f"""<|system|>
You are an expert cloud computing content creator writing a LinkedIn post about Azure AI.

Guidelines:
- Write in enthusiastic, professional tone
- Use simple analogies for complex concepts
- Include practical, actionable insights
- Add relevant emojis and bullet points
- Keep under 1300 characters
- End with engaging question

</|system|>
<|user|>
Write a LinkedIn post about these Azure AI updates:

{context}
</|user|>
<|assistant|>
"""
        
        try:
            # Generate text
            result = self.generator(
                prompt,
                max_new_tokens=400,
                temperature=0.7,
                do_sample=True,
                top_p=0.9
            )
            
            # Extract generated text
            if isinstance(result, list):
                generated = result[0]['generated_text']
            else:
                generated = result
            
            # Remove prompt from output
            post = generated.replace(prompt, '').strip()
            
            # Clean up the post
            post = self._clean_post(post)
            
            return post
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._template_generate(news)
    
    def _template_generate(self, news: List[Dict]) -> str:
        """Generate post using templates (reliable fallback)"""
        if not news:
            # Default post when no news available
            return self._get_default_post()
        
        # Get most relevant news item
        main_news = news[0]
        
        # Determine which template to use
        if any(keyword in main_news['title'].lower() for keyword in ['release', 'announce', 'launch', 'new']):
            template = self.TEMPLATES['new_release']
        else:
            template = self.TEMPLATES['general_update']
        
        # Extract hashtags from content
        extra_tags = ' '.join(self._extract_hashtags(main_news))
        
        # Fill template
        post = template.format(
            title=main_news['title'],
            summary=main_news['summary'][:200],
            link=main_news.get('link', 'https://azure.microsoft.com'),
            extra_tags=extra_tags
        )
        
        # Clean and ensure length limit
        return self._clean_post(post)[:1300]
    
    def _prepare_context(self, news: List[Dict], max_items: int = 3) -> str:
        """Prepare news context for LLM"""
        context = "Recent Azure AI news:\n\n"
        
        for i, item in enumerate(news[:max_items], 1):
            context += f"{i}. Title: {item['title']}\n"
            context += f"   Summary: {item['summary'][:150]}...\n\n"
        
        return context
    
    def _clean_post(self, text: str) -> str:
        """Clean and optimize post content"""
        # Remove multiple newlines
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove excessive spaces
        text = re.sub(r' {2,}', ' ', text)
        
        # Ensure hashtag formatting
        text = re.sub(r'#(\w+)', r'#\1', text)
        
        # Add default hashtags if none present
        if not re.search(r'#\w+', text):
            text += '\n\n#MicrosoftAzure #AI #CloudComputing #AzureAI'
        
        return text.strip()
    
    def _extract_hashtags(self, news: Dict) -> List[str]:
        """Extract relevant hashtags from news"""
        hashtags = ['#MicrosoftAzure', '#AzureAI']
        
        text = (news.get('title', '') + ' ' + news.get('summary', '')).lower()
        
        hashtag_map = {
            'openai': '#OpenAI',
            'copilot': '#MicrosoftCopilot',
            'gpt': '#GPT',
            'machine learning': '#MachineLearning',
            'cognitive': '#CognitiveServices',
            'security': '#CloudSecurity',
            'kubernetes': '#Kubernetes',
            'devops': '#DevOps'
        }
        
        for keyword, tag in hashtag_map.items():
            if keyword in text and tag not in hashtags:
                hashtags.append(tag)
        
        return hashtags[:3]  # Limit to 3 extra hashtags
    
    def _get_default_post(self) -> str:
        """Generate default post when no news is available"""
        return """🚀 Getting Started with Azure AI: A Beginner's Guide

I've been exploring Microsoft Azure AI services, and I'm amazed at how accessible they've become!

💡 **Simple Analogy**: Think of Azure AI like a restaurant kitchen:
• You don't need to know how to cook (complex ML algorithms)
• You just order what you want (choose an AI service)
• The kitchen handles everything (Azure infrastructure)
• You enjoy the delicious results (intelligent applications)

🎯 **3 Ways to Start Today**:
1. **Azure OpenAI Service** - Add ChatGPT-like capabilities to your apps
2. **Cognitive Services** - See, hear, speak, and understand your users
3. **Azure Machine Learning** - Build custom AI models without deep expertise

📊 **Why This Matters**: 
The barrier to AI adoption is lower than ever. Small teams can now compete with tech giants!

🔗 Start your AI journey: https://azure.microsoft.com/free

What would you build with AI? Share your ideas below! 👇

#MicrosoftAzure #AI #CloudComputing #Innovation #TechForEveryone"""
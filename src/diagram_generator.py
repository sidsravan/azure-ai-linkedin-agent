import subprocess
from pathlib import Path

class DiagramGenerator:
    """Generate architecture diagrams using D2"""
    
    def generate_azure_ai_diagram(self):
        """Create architecture diagram for Azure AI services"""
        d2_code = """
        direction: right
        title: Azure AI Services Architecture
        
        user: User Application {
          shape: rectangle
        }
        
        gateway: API Gateway {
          shape: rectangle
        }
        
        azure_ai: Azure AI Services {
          cognitive: Cognitive Services
          openai: Azure OpenAI
          ml: Machine Learning
        }
        
        storage: Data Storage {
          blob: Blob Storage
          cosmos: Cosmos DB
        }
        
        user -> gateway -> azure_ai
        azure_ai -> storage
        """
        
        # Save D2 file
        Path('diagrams/azure_ai.d2').parent.mkdir(exist_ok=True)
        with open('diagrams/azure_ai.d2', 'w') as f:
            f.write(d2_code)
        
        # Generate SVG (requires D2 installed)
        subprocess.run(['d2', 'diagrams/azure_ai.d2', 'diagrams/azure_ai.svg'])
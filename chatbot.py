import streamlit as st
import os
from dotenv import load_dotenv
from google import genai

def show_chatbot():
    """Display the chatbot interface for fitness advice and support."""
    st.title("Fitness Chatbot")
    
    st.write("Ask me anything about fitness, exercises, diet, nutrition, or workout tips!")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your question here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate chatbot response (Gemini-backed with graceful fallback)
        response = get_chatbot_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)


def _get_gemini_chat():
    """Create or retrieve a Gemini chat session configured from environment.

    Returns None if the API key is missing or configuration fails.
    """
    if "gemini_chat" in st.session_state:
        return st.session_state.gemini_chat

    # Load environment variables from .env if present
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    try:
        # Create client with new google.genai API
        client = genai.Client(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        # System instruction for the chatbot
        system_instruction = """You are a knowledgeable fitness and nutrition assistant. Your expertise includes:
        
        - Exercise techniques, form, and workout routines for all fitness levels
        - Nutritional guidance including macronutrients (proteins, carbs, fats) and micronutrients (vitamins, minerals)
        - Calorie counting and dietary recommendations for different fitness goals (weight loss, muscle gain, maintenance)
        - Meal planning and healthy eating habits
        - Nutritional values of common foods and beverages
        - Supplement information and when they might be beneficial
        - Recovery, rest, and injury prevention
        
        Provide accurate, helpful, and evidence-based advice. Be encouraging and supportive. 
        Always remind users to consult healthcare professionals for medical concerns or before starting new diets/exercise programs."""

        # Build config with system instruction
        config = {"system_instruction": system_instruction}
        
        # Store client and config in session state for chat
        st.session_state.gemini_client = client
        st.session_state.gemini_model = model_name
        st.session_state.gemini_config = config
        st.session_state.gemini_chat = True
        return True
    except Exception as e:
        # Any configuration or SDK error -> fall back to rule-based replies
        st.warning(f"Could not connect to Gemini API: {str(e)}")
        return None

def get_chatbot_response(user_input: str) -> str:
    """Generate chatbot response using Gemini when available, else a simple fallback."""

    # Try Gemini first
    chat = _get_gemini_chat()
    if chat is not None:
        try:
            client = st.session_state.gemini_client
            model_name = st.session_state.gemini_model
            config = st.session_state.gemini_config
            
            # Build conversation history
            contents = []
            for m in st.session_state.get("messages", []):
                role = m.get("role", "")
                content = m.get("content", "")
                if content:
                    # Map streamlit roles to genai roles
                    if role == "user":
                        contents.append({"role": "user", "parts": [{"text": content}]})
                    elif role == "assistant":
                        contents.append({"role": "model", "parts": [{"text": content}]})
            
            # Add current user input
            contents.append({"role": "user", "parts": [{"text": user_input}]})
            
            # Generate response
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            # Fall back to heuristic responses silently (quota or API issues)
            error_msg = str(e).lower()
            if "quota" in error_msg or "resource_exhausted" in error_msg:
                # Silently fall back for quota issues
                pass
            else:
                # Show other errors briefly
                st.warning("Using offline mode due to API unavailability")
            pass

    # Fallback: Simple heuristic responses
    user_input_lower = user_input.lower()
    
    # Exercise-related questions
    if any(word in user_input_lower for word in ["squat", "leg"]):
        return """🏋️ **How to do Squats:**
        
1. Stand with feet shoulder-width apart
2. Keep your chest up and core engaged
3. Lower your body by bending knees and hips
4. Go down until thighs are parallel to ground
5. Push through your heels to stand back up

**Benefits:** Strengthens legs, glutes, and core. Great for overall lower body development!"""
    
    if any(word in user_input_lower for word in ["pushup", "push up", "chest"]):
        return """💪 **How to do Push-ups:**
        
1. Start in plank position, hands shoulder-width apart
2. Keep body straight from head to heels
3. Lower chest to ground by bending elbows
4. Push back up to starting position

**Benefits:** Works chest, shoulders, triceps, and core!"""
    
    if any(word in user_input_lower for word in ["curl", "arm", "bicep"]):
        return "💪 Curls work your biceps! Keep elbows at sides, control the weight, and squeeze at the top. Start with 3 sets of 10-12 reps."
    
    # Nutrition-related questions
    if "banana" in user_input_lower:
        return """🍌 **Nutritional Info for Bananas:**
        
One medium banana (118g):
- **Calories:** ~105
- **Carbs:** 27g (including 14g sugar, 3g fiber)
- **Protein:** 1.3g
- **Fat:** 0.4g
- **Potassium:** 422mg (great for muscle function!)

A dozen bananas = **~1,260 calories**

Bananas are excellent pre/post-workout snacks for quick energy!"""
    
    if any(word in user_input_lower for word in ["calorie", "calories"]):
        return """📊 **Calorie Guidelines:**
        
- Average adult: 2000-2500 calories/day
- Weight loss: 500 calorie deficit/day
- Muscle gain: 300-500 calorie surplus/day

What specific food are you asking about? I can provide nutritional details!"""
    
    if any(word in user_input_lower for word in ["protein", "macro"]):
        return """🥩 **Protein Guidelines:**
        
- Sedentary: 0.8g per kg body weight
- Active: 1.2-1.6g per kg
- Muscle building: 1.6-2.2g per kg

Good sources: chicken, fish, eggs, beans, Greek yogurt, tofu"""
    
    if any(word in user_input_lower for word in ["diet", "meal", "eating"]):
        return """🥗 **Healthy Eating Tips:**
        
- Balance proteins, carbs, and healthy fats
- Eat plenty of vegetables and fruits
- Stay hydrated (8+ glasses of water daily)
- Plan meals ahead to avoid unhealthy choices
- Eat whole foods over processed options

What are your specific fitness goals?"""
    
    # General fitness
    if any(word in user_input_lower for word in ["form", "technique", "correct"]):
        return "✅ Good form is crucial! Proper technique prevents injuries and maximizes results. Focus on controlled movements rather than speed or heavy weights."
    
    if any(word in user_input_lower for word in ["rep", "repetition", "set"]):
        return """📈 **Rep & Set Guidelines:**
        
- Beginners: 3 sets of 8-12 reps
- Strength: 3-5 sets of 4-6 reps (heavier weight)
- Endurance: 3-4 sets of 15-20 reps (lighter weight)
- Hypertrophy (muscle growth): 3-4 sets of 8-12 reps"""

    return "I'm here to help with fitness, exercise, nutrition, and diet questions! You can ask me about exercise techniques, workout routines, nutritional values, meal planning, or healthy eating tips. What would you like to know? 💪🥗"

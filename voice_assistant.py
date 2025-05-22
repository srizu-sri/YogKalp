import pyttsx3
import threading
import queue

class VoiceAssistant:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Speed of speech
        self.engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
        
        # Try to set a female voice if available
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "female" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.speech_thread = None
        self.enabled = True
        
        # Start the speech processing thread
        self.start_speech_thread()
    
    def start_speech_thread(self):
        """Start a background thread to process speech queue"""
        self.speech_thread = threading.Thread(target=self._process_speech_queue, daemon=True)
        self.speech_thread.start()
    
    def _process_speech_queue(self):
        """Process speech items from the queue"""
        while True:
            try:
                # Get the next text to speak from the queue
                text = self.speech_queue.get()
                
                if text is None:  # None is a signal to stop
                    break
                    
                if self.enabled:  # Only speak if enabled
                    self.is_speaking = True
                    self.engine.say(text)
                    self.engine.runAndWait()
                    self.is_speaking = False
                    
                # Mark this task as done
                self.speech_queue.task_done()
                
            except Exception as e:
                print(f"Error in speech thread: {e}")
                self.is_speaking = False
    
    def speak(self, text):
        """Add text to the speech queue"""
        if text and self.enabled:
            self.speech_queue.put(text)
    
    def stop(self):
        """Stop current speech and clear queue"""
        self.engine.stop()
        
        # Clear the queue
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except queue.Empty:
                break
                
        self.is_speaking = False
    
    def toggle(self):
        """Toggle voice assistant on/off"""
        self.enabled = not self.enabled
        
        if not self.enabled:
            self.stop()
            
        return self.enabled
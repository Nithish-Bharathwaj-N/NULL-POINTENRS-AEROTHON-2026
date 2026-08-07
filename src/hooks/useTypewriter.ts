import { useState, useEffect } from 'react';
import { audio } from '../utils/audioEngine';

export function useTypewriter(text: string, speedMs: number = 30) {
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    let i = 0;
    setDisplayedText('');
    
    // Only play audio if we're actually typing something new
    if (!text) return;

    const interval = setInterval(() => {
      setDisplayedText((prev) => {
        const nextChar = text.charAt(i);
        if (nextChar !== ' ' && nextChar !== '█') {
          audio.playKeystroke();
        }
        return prev + nextChar;
      });
      
      i++;
      if (i >= text.length) {
        clearInterval(interval);
      }
    }, speedMs);

    return () => clearInterval(interval);
  }, [text, speedMs]);

  // Add a blinking cursor at the end
  const isComplete = displayedText.length === text.length;
  const cursor = isComplete ? '' : '█';

  return displayedText + cursor;
}

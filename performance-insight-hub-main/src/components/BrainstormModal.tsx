import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { Send, X, Sparkles } from 'lucide-react';
import { useState } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface BrainstormModalProps {
  isOpen: boolean;
  onClose: () => void;
  applicationName: string;
}

export const BrainstormModal = ({ isOpen, onClose, applicationName }: BrainstormModalProps) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: `I'm here to help you analyze the performance issues with ${applicationName}. What specific aspects would you like to explore?

Some areas we can discuss:
• Database query optimization strategies
• Caching implementation approaches
• Infrastructure scaling options
• Code-level bottleneck identification
• Monitoring and alerting improvements`
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const responses = [
        "Based on the metrics, I recommend implementing connection pooling with a maximum of 20 connections and a connection timeout of 30 seconds. This should help reduce the database connection exhaustion issues.",
        "The response time spikes correlate with high memory usage. Consider implementing a caching layer using Redis to reduce database queries by approximately 40-60%.",
        "I suggest adding composite indexes on the frequently queried columns. Analyzing the slow query logs would help identify which specific queries need optimization.",
        "Consider horizontal scaling by adding 2 more instances behind a load balancer. This would distribute the load and improve throughput by approximately 3x."
      ];
      
      const aiMessage: Message = {
        role: 'assistant',
        content: responses[Math.floor(Math.random() * responses.length)]
      };
      
      setMessages(prev => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl h-[80vh] p-0 flex flex-col">
        <DialogHeader className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-xl font-bold flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              AI Brainstorm: {applicationName}
            </DialogTitle>
            <Button variant="outline" onClick={onClose} size="icon">
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>

        <ScrollArea className="flex-1 px-6">
          <div className="space-y-4 py-6">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <Card
                  className={`p-4 max-w-[80%] ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-card'
                  }`}
                >
                  <p className="text-sm whitespace-pre-line">{message.content}</p>
                </Card>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <Card className="p-4 max-w-[80%] bg-card">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </Card>
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="p-6 border-t bg-background">
          <div className="flex gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask about optimization strategies, root causes, or potential solutions..."
              className="min-h-[60px] resize-none"
            />
            <Button onClick={handleSend} disabled={!input.trim() || isTyping}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

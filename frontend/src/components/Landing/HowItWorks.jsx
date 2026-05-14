import { motion } from 'motion';
import { Link2, Sparkles, Zap } from 'lucide-react';

const steps = [
  {
    icon: <Link2 className="w-10 h-10 text-brand-blue" />,
    title: "Connect (ä¸€?µä¸²??",
    description: "OAuth2 ?ˆæ?ï¼Œå¿«?Ÿé€?? Google ??Facebookï¼Œç„¡?€è¤‡é?è¨­å???
  },
  {
    icon: <Sparkles className="w-10 h-10 text-brand-purple" />,
    title: "Analyze (?ªå?å½™æ•´)",
    description: "å°ˆå±¬å·¥ä??€ï¼ŒæŸ¥?‹è‡ª?•å??¸æ?è¦–å?ï¼ŒAI ?³æ??²è??¸æ?æ¸…æ??‡å»ºæ¨¡ã€?
  },
  {
    icon: <Zap className="w-10 h-10 text-brand-cyan" />,
    title: "Strategize (?°ç•¥?ºæ?)",
    description: "?¼å« AI ?†æ?å¸«ï??²å??¯ç??³åŸ·è¡Œç??ªå?ç­–ç•¥ï¼Œæ¶ä½”å??´å?æ©Ÿã€?
  }
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 px-6 relative">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-20">
          <h2 className="text-3xl md:text-5xl font-display font-bold mb-4">ç°¡å–®ä¸‰æ­¥ä¸Šæ?</h2>
          <p className="text-slate-400 max-w-xl mx-auto">å¾æ··äº‚åˆ°æ¸…æ™°ï¼Œåª?€å¹¾å??˜ã€?/p>
        </div>

        <div className="relative">
          {/* Connector Line */}
          <div className="hidden md:block absolute top-1/2 left-20 right-20 h-0.5 bg-gradient-to-r from-brand-blue via-brand-purple to-brand-cyan opacity-20 -translate-y-1/2 -z-10" />
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {steps.map((item, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.2 }}
                className="relative flex flex-col items-center text-center"
              >
                <div className="w-20 h-20 rounded-full glass border-white/20 flex items-center justify-center mb-8 relative bg-slate-900 group shadow-xl">
                  <div className="absolute -inset-2 bg-gradient-to-tr from-brand-blue to-brand-purple rounded-full opacity-0 group-hover:opacity-20 transition-opacity blur-md" />
                  <span className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-slate-800 border border-white/10 flex items-center justify-center text-xs font-bold text-white z-10 shadow-lg">0{index + 1}</span>
                  {item.icon}
                </div>
                <h3 className="text-2xl font-bold text-white mb-4">{item.title}</h3>
                <p className="text-slate-400 max-w-xs">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}


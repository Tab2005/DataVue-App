import { motion } from 'motion';
import { Search, Facebook, BarChart3, Bot } from 'lucide-react';

const features = [
  {
    icon: <Search className="w-8 h-8 text-blue-400" />,
    title: "GSC ?œå??å?æ´å?",
    description: "æ·±å…¥?œéµå­—æˆ°?´ï??Œæ¡?—çœ¾?Ÿå¯¦?„æ?å°‹å?æ©Ÿè??å?ï¼Œè€Œä??…å??¯æ??ã€?,
    color: "from-blue-500/20 to-transparent"
  },
  {
    icon: <Facebook className="w-8 h-8 text-cyan-400" />,
    title: "Facebook Ads ç²¾æ?è¿½è¹¤",
    description: "ä¸€?®ä??¶ç?å»??è¡¨ç¾è¿½è¹¤ï¼Œå¯¦?‚å„ª?–è??–æ??¬ï??’ç??ç?æµªè²»??,
    color: "from-cyan-500/20 to-transparent"
  },
  {
    icon: <BarChart3 className="w-8 h-8 text-purple-400" />,
    title: "GA4 ?¨æ–¹ä½æ??å???,
    description: "?„å??¨æˆ¶ç¶²ç?è¡Œç‚ºè·¯å?ï¼Œé€²è?æ·±åº¦?„å…§å®¹å?çµ„å„ª?–ï??å?è·³å‡º?‡è¡¨?¾ã€?,
    color: "from-purple-500/20 to-transparent"
  },
  {
    icon: <Bot className="w-8 h-8 text-emerald-400" />,
    title: "Site-tegy AI Hub",
    description: "24å°æ? AI ?†æ?å¸«ï??´å?å¤šæ??¸æ?ï¼Œç”¢?ºå…·?™ã€Œå?è² æ??ç??·é??ªå??‡ä»¤??,
    color: "from-emerald-500/20 to-transparent"
  }
];

export default function Features() {
  return (
    <section id="features" className="py-24 px-6 relative overflow-hidden">
      {/* Decorative Orbs */}
      <div className="absolute top-1/2 left-0 w-64 h-64 bg-brand-blue/5 rounded-full blur-[100px]" />
      <div className="absolute bottom-0 right-0 w-64 h-64 bg-brand-purple/5 rounded-full blur-[100px]" />

      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-display font-bold mb-4">?¸å??Ÿèƒ½</h2>
          <p className="text-slate-400 max-w-xl mx-auto">å¼·å¤§?„æ¨¡çµ„å?å·¥å…·ï¼Œç‚º?¨ç?æ¥­å?å¢é•·?ä??•å???/p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <motion.div 
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              whileHover={{ y: -10 }}
              className={`glass rounded-3xl p-8 border-white/5 relative overflow-hidden group bg-gradient-to-br ${feature.color}`}
            >
              <div className="mb-6 bg-white/5 w-16 h-16 rounded-2xl flex items-center justify-center border border-white/10 group-hover:scale-110 transition-transform duration-500">
                {feature.icon}
              </div>
              <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed group-hover:text-slate-300 transition-colors">
                {feature.description}
              </p>
              
              {/* Corner Glow */}
              <div className="absolute -bottom-2 -right-2 w-12 h-12 bg-white/5 rounded-full blur-xl group-hover:bg-white/10 transition-colors" />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}


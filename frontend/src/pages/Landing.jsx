import { useEffect } from 'react';
import Navbar from '../components/Landing/Navbar';
import Hero from '../components/Landing/Hero';
import PainPoints from '../components/Landing/PainPoints';
import Features from '../components/Landing/Features';
import Audience from '../components/Landing/Audience';
import HowItWorks from '../components/Landing/HowItWorks';
import Footer from '../components/Landing/Footer';
import '../landing.css';

export default function Landing() {
  // Simple scroll reveal implementation for elements with 'reveal' class
  useEffect(() => {
    const observerOptions = {
      root: null,
      rootMargin: '0px',
      threshold: 0.1
    };

    const handleIntersect = (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('active');
        }
      });
    };

    const observer = new IntersectionObserver(handleIntersect, observerOptions);
    const elements = document.querySelectorAll('.reveal');
    elements.forEach(el => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  return (
    <div className="min-h-screen bg-[#050508] selection:bg-brand-blue/30 selection:text-white">
      <Navbar />
      
      <main>
        <Hero />
        
        <div className="reveal">
          <PainPoints />
        </div>
        
        <div className="reveal">
          <Features />
        </div>
        
        <div className="reveal">
          <Audience />
        </div>
        
        <div className="reveal">
          <HowItWorks />
        </div>
      </main>

      <Footer />

      {/* Subtle Background Noice/Grain Overlay */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.03] z-[9999] bg-[url('https://grainy-gradients.vercel.app/noise.svg')]" />
    </div>
  );
}


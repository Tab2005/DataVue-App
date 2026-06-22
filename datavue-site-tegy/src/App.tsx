/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect } from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import PainPoints from './components/PainPoints';
import Features from './components/Features';
import Audience from './components/Audience';
import HowItWorks from './components/HowItWorks';
import Footer from './components/Footer';

export default function App() {
  // Simple scroll reveal implementation for elements with 'reveal' class
  useEffect(() => {
    const observerOptions = {
      root: null,
      rootMargin: '0px',
      threshold: 0.1
    };

    const handleIntersect = (entries: IntersectionObserverEntry[]) => {
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

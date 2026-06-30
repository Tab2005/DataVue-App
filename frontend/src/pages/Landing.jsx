import Navbar from '../components/Landing/Navbar';
import Hero from '../components/Landing/Hero';
import LogoBar from '../components/Landing/LogoBar';
import Features from '../components/Landing/Features';
import PainPoints from '../components/Landing/PainPoints';
import MetaAndromeda from '../components/Landing/MetaAndromeda';
import Audience from '../components/Landing/Audience';
import SocialProof from '../components/Landing/SocialProof';
import HowItWorks from '../components/Landing/HowItWorks';
import FinalCTA from '../components/Landing/FinalCTA';
import Footer from '../components/Landing/Footer';

export default function Landing() {
  return (
    <div className="landing-page-root min-h-screen selection:bg-cyan-500/30 selection:text-white">
      <Navbar />

      <main>
        <Hero />
        <LogoBar />
        <Features />
        <PainPoints />
        <MetaAndromeda />
        <Audience />
        <SocialProof />
        <HowItWorks />
        <FinalCTA />
      </main>

      <Footer />

      {/* 背景顆粒噪點疊加層 */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.015] z-[9999] bg-[url('https://grainy-gradients.vercel.app/noise.svg')]" />
    </div>
  );
}
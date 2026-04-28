import Hero from "@/components/Hero";
import FeatureShowcase from "@/components/FeatureShowcase";
import AgentsGrid from "@/components/AgentsGrid";
import FAQ from "@/components/FAQ";
import TrustStrip from "@/components/TrustStrip";

export default function Page() {
  return (
    <main>
      <Hero />
      <FeatureShowcase />
      <AgentsGrid />
      <FAQ />
      <TrustStrip />
    </main>
  );
}

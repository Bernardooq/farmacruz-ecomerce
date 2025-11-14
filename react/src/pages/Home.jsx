import Header from '../layout/Header';
import Footer from '../layout/Footer';
import Hero from '../components/Hero';
import IntroText from '../components/IntroText';
import FeaturedProducts from '../components/FeaturedProducts';
import Advantages from '../components/Advantages';

export default function Home() {
  return (
    <>
      <Header />
      <main>
        <Hero />
        <IntroText />
        <FeaturedProducts />
        <Advantages />
      </main>
      <Footer />
    </>
  );
}
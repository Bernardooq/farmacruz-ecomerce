import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTruckFast, faBoxOpen, faHeadset } from '@fortawesome/free-solid-svg-icons';

export default function Advantages() {
  const items = [
    {
      icon: faTruckFast,
      title: 'Entregas Rápidas',
      text: 'Logística optimizada para recibir tus pedidos en tiempo récord.',
    },
    {
      icon: faBoxOpen,
      title: 'Amplio Catálogo',
      text: 'Miles de productos de los laboratorios más reconocidos.',
    },
    {
      icon: faHeadset,
      title: 'Soporte Dedicado',
      text: 'Atención personalizada para resolver todas tus dudas.',
    },
  ];

  return (
    <section className="advantages">
      <div className="container">
        <h2 className="section-title">¿Por Qué Elegirnos?</h2>
        <div className="advantages-grid">
          {items.map((item, index) => (
            <div className="advantage-item" key={index}>
              <FontAwesomeIcon icon={item.icon} className="advantage-item__icon" />
              <h3 className="advantage-item__title">{item.title}</h3>
              <p>{item.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
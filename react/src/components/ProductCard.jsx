import React from 'react';

export default function ProductCard({ image, name, category, stock, isAvailable }) {
  return (
    <article className="product-card">
      <img src={image} alt={name} className="product-card__image" />
      <div className="product-card__info">
        <h3 className="product-card__name">{name}</h3>
        <p className="product-card__category">{category}</p>
        <p className="product-card__stock">
          {isAvailable ? (
            <>En stock: <strong>{stock} unidades</strong></>
          ) : (
            <>Agotado</>
          )}
        </p>
        <button className="product-card-details__button">Ver Detalles</button>
        <button
          className="product-card__button"
          disabled={!isAvailable}
        >
          Agregar al Carrito
        </button>
      </div>
    </article>
  );
}
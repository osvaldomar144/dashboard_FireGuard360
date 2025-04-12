// Gestisce il caricamento degli eventi per la progress bar di <model-viewer>
const onProgress = (event) => {
  const progressBar = event.target.querySelector('.progress-bar');
  const updatingBar = event.target.querySelector('.update-bar');
  updatingBar.style.width = `${event.detail.totalProgress * 100}%`;
  if (event.detail.totalProgress === 1) {
    progressBar.classList.add('hide');
    event.target.removeEventListener('progress', onProgress);
  } else {
    progressBar.classList.remove('hide');
  }
};
document.querySelector('model-viewer').addEventListener('progress', onProgress);

// Esegue una richiesta per ottenere i dati degli hotspot dal server
fetch('/get_hotspot_status')
  .then(response => response.json())
  .then(data => {
    // Cambia il colore dell'etichetta e del pallino in base allo stato dei dispositivi (arduino)
    
    // Hotspot per la cucina
    const hotspot3 = document.querySelector('#hotspot-3');
    const hotspot3Annotation = hotspot3.querySelector('.HotspotAnnotation');
    if (hotspot3 && hotspot3Annotation) {
      if (data.arduino1 === 1) {
        hotspot3Annotation.style.backgroundColor = 'rgba(255, 0, 0, 0.5)'; // Rosso trasparente pericolo in cucina
        hotspot3.style.borderColor = 'rgba(255, 0, 0, 0.5)'; // Bordo rosso per il pallino
      } else {
        hotspot3Annotation.style.backgroundColor = 'rgba(255, 255, 255, 0.8)'; // Colore neutro
        hotspot3.style.borderColor = 'rgba(255, 255, 255, 0.5)'; // Colore neutro per il bordo del pallino
      }
    }

    // Hotspot per la camera da letto
    const hotspot5 = document.querySelector('#hotspot-5');
    const hotspot5Annotation = hotspot5.querySelector('.HotspotAnnotation');
    if (hotspot5 && hotspot5Annotation) {
      if (data.arduino2 === 1) {
        hotspot5Annotation.style.backgroundColor = 'rgba(255, 0, 0, 0.5)'; // Rosso trasparente pericolo in camera da letto
        hotspot5.style.borderColor = 'rgba(255, 0, 0, 0.5)'; // Bordo rosso per il pallino
      } else {
        hotspot5Annotation.style.backgroundColor = 'rgba(255, 255, 255, 0.8)'; // Colore neutro
        hotspot5.style.borderColor = 'rgba(255, 255, 255, 0.5)'; // Colore neutro per il bordo del pallino
      }
    }

    // Hotspot per il giardino
    const hotspot7 = document.querySelector('#hotspot-7');
    const hotspot7Annotation = hotspot7.querySelector('.HotspotAnnotation');
    if (hotspot7 && hotspot7Annotation) {
      if (data.arduino3 === 1) {
        hotspot7Annotation.style.backgroundColor = 'rgba(255, 0, 0, 0.5)'; // Rosso trasparente pericolo in giardino
        hotspot7.style.borderColor = 'rgba(255, 0, 0, 0.5)'; // Bordo rosso per il pallino
      } else {
        hotspot7Annotation.style.backgroundColor = 'rgba(255, 255, 255, 0.8)'; // Colore neutro
        hotspot7.style.borderColor = 'rgba(255, 255, 255, 0.5)'; // Colore neutro per il bordo del pallino
      }
    }

    // Hotspot per il soggiorno
    const hotspot11 = document.querySelector('#hotspot-11');
    const hotspot11Annotation = hotspot11.querySelector('.HotspotAnnotation');
    if (hotspot11 && hotspot11Annotation) {
      if (data.arduino4 === 1) {
        hotspot11Annotation.style.backgroundColor = 'rgba(255, 0, 0, 0.5)'; // Rosso trasparente pericolo nel soggiorno
        hotspot11.style.borderColor = 'rgba(255, 0, 0, 0.5)'; // Bordo rosso per il pallino
      } else {
        hotspot11Annotation.style.backgroundColor = 'rgba(255, 255, 255, 0.8)'; // Colore neutro
        hotspot11.style.borderColor = 'rgba(255, 255, 255, 0.5)'; // Colore neutro per il bordo del pallino
      }
    }
  })
  .catch(error => console.error('Errore nel recupero dei dati:', error));
// Aggiunge l'evento di clic sugli hotspot per toggle la visibilità delle etichette e il contorno azzurro
document.querySelectorAll('.Hotspot').forEach(hotspot => {
  hotspot.addEventListener('click', () => {
    const isSelected = hotspot.classList.contains('selected');

    document.querySelectorAll('.Hotspot').forEach(h => {
      h.classList.remove('visible', 'selected', 'animate-in');
    });

    if (!isSelected) {
      hotspot.classList.add('visible', 'selected', 'animate-in');

      // Rimuove 'animate-in' dopo un tick così la transizione in uscita funziona
      setTimeout(() => {
        hotspot.classList.remove('animate-in');
      }, 10);
    }
  });
});
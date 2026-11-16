// Minichat del asistente sobre Ollama (RAG con streaming)
(() => {
    const API_ASISTENTE = 'asistente.php';
    const MENSAJES_DE_HISTORIAL = 6;
    const SALUDO = 'El corazón de IA de este proyecto funciona con Ollama, una herramienta que ' +
        'ejecuta modelos de inteligencia artificial en local, sin enviar datos a internet. ' +
        'Aquí clasifica las consultas con el modelo llama3.2:3b. ¿Quieres saber un poco más?';

    const botonAbrir = document.getElementById('asistente-boton');
    const ventana = document.getElementById('asistente');
    const botonCerrar = document.getElementById('asistente-cerrar');
    const cajaMensajes = document.getElementById('asistente-mensajes');
    const sugerencias = document.getElementById('asistente-sugerencias');
    const formulario = document.getElementById('asistente-formulario');
    const campoPregunta = document.getElementById('asistente-pregunta');
    const botonEnviar = document.getElementById('asistente-enviar');

    // La memoria de la conversación vive aquí, en el navegador
    const historial = [];

    /** Añade un mensaje al chat. Se usa textContent: el texto nunca se interpreta como HTML. */
    function anadirMensaje(rol, texto) {
        const mensaje = document.createElement('div');
        mensaje.className = `mensaje mensaje-${rol}`;
        const parrafo = document.createElement('p');
        parrafo.textContent = texto;
        mensaje.appendChild(parrafo);
        cajaMensajes.appendChild(mensaje);
        cajaMensajes.scrollTop = cajaMensajes.scrollHeight;
        return mensaje;
    }

    function mostrarFuentes(mensaje, fuentes) {
        const caja = document.createElement('div');
        caja.className = 'fuentes';
        caja.textContent = 'Fuentes: ' + fuentes.join(' · ');
        mensaje.appendChild(caja);
    }

    /** Envía la pregunta y va pintando la respuesta a medida que llega. */
    async function preguntar(pregunta) {
        campoPregunta.disabled = true;
        botonEnviar.disabled = true;
        sugerencias.classList.add('oculto');

        anadirMensaje('user', pregunta);
        const mensaje = anadirMensaje('assistant', 'Buscando en la documentación…');
        const parrafo = mensaje.querySelector('p');
        mensaje.classList.add('pensando');

        let respuesta = '';
        let fuentes = [];
        let huboError = false;

        try {
            const peticion = await fetch(API_ASISTENTE, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pregunta, historial: historial.slice(-MENSAJES_DE_HISTORIAL) }),
            });

            // Leemos la respuesta a trozos: cada línea completa es un evento JSON
            const lector = peticion.body.getReader();
            const decodificador = new TextDecoder();
            let pendiente = '';

            while (true) {
                const { done, value } = await lector.read();
                if (done) break;
                pendiente += decodificador.decode(value, { stream: true });
                const lineas = pendiente.split('\n');
                pendiente = lineas.pop();  // la última puede estar a medias

                for (const linea of lineas) {
                    if (!linea.trim()) continue;
                    const evento = JSON.parse(linea);

                    if (evento.tipo === 'fuentes') {
                        fuentes = evento.fuentes;
                    } else if (evento.tipo === 'texto') {
                        respuesta += evento.contenido;
                        mensaje.classList.remove('pensando');
                        parrafo.textContent = respuesta;
                        cajaMensajes.scrollTop = cajaMensajes.scrollHeight;
                    } else if (evento.tipo === 'error') {
                        huboError = true;
                        mensaje.classList.remove('pensando');
                        mensaje.classList.add('mensaje-error');
                        parrafo.textContent = evento.mensaje;
                    }
                }
            }
        } catch (error) {
            huboError = true;
            mensaje.classList.remove('pensando');
            mensaje.classList.add('mensaje-error');
            parrafo.textContent = 'No se ha podido conectar con el asistente.';
        }

        if (!huboError && respuesta) {
            historial.push({ rol: 'user', contenido: pregunta });
            historial.push({ rol: 'assistant', contenido: respuesta.trim() });
            if (fuentes.length) mostrarFuentes(mensaje, fuentes);
        }

        campoPregunta.disabled = false;
        botonEnviar.disabled = false;
        campoPregunta.focus();
        cajaMensajes.scrollTop = cajaMensajes.scrollHeight;
    }

    // Abrir y cerrar el chat
    botonAbrir.addEventListener('click', () => {
        ventana.classList.toggle('oculto');
        if (!ventana.classList.contains('oculto')) campoPregunta.focus();
    });
    botonCerrar.addEventListener('click', () => ventana.classList.add('oculto'));

    // Preguntas sugeridas
    sugerencias.addEventListener('click', (evento) => {
        if (evento.target.tagName === 'BUTTON') preguntar(evento.target.textContent);
    });

    // Pregunta escrita
    formulario.addEventListener('submit', (evento) => {
        evento.preventDefault();
        const pregunta = campoPregunta.value.trim();
        if (!pregunta) return;
        campoPregunta.value = '';
        preguntar(pregunta);
    });

    anadirMensaje('assistant', SALUDO);
})();
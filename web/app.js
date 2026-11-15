const API = 'api.php';

const CATEGORIAS = [
    { nombre: 'Soporte Técnico', clase: 'soporte' },
    { nombre: 'Duda Comercial', clase: 'comercial' },
    { nombre: 'Agradecimiento', clase: 'gracias' },
];

// Elementos de la página
const formulario = document.getElementById('formulario');
const campoTexto = document.getElementById('texto');
const boton = document.getElementById('boton');
const resultado = document.getElementById('resultado');
const cajaContadores = document.getElementById('contadores');
const listado = document.getElementById('listado');
const botonAnterior = document.getElementById('anterior');
const botonSiguiente = document.getElementById('siguiente');
const infoPagina = document.getElementById('info-pagina');

// Estado de la vista: qué página y qué filtro se están viendo
let paginaActual = 1;
let totalPaginas = 1;
let categoriaFiltro = '';

/** Evita que el texto de un cliente se interprete como HTML (protección XSS). */
function escaparHTML(texto) {
    const div = document.createElement('div');
    div.textContent = texto ?? '';
    return div.innerHTML;
}

function claseCategoria(categoria) {
    const encontrada = CATEGORIAS.find(c => c.nombre === categoria);
    return encontrada ? encontrada.clase : 'sin-clasificar';
}

function formatearFecha(fecha) {
    return new Date(fecha.replace(' ', 'T')).toLocaleString('es-ES', {
        day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
    });
}

// ---------------------------------------------------------------------------
// Listado, contadores y paginación
// ---------------------------------------------------------------------------

/** Pide a PHP la página y el filtro actuales, y lo pinta todo. */
async function cargarConsultas() {
    const parametros = new URLSearchParams({ pagina: paginaActual });
    if (categoriaFiltro) parametros.set('categoria', categoriaFiltro);

    const respuesta = await fetch(`${API}?${parametros}`);
    const datos = await respuesta.json();

    totalPaginas = datos.paginas;
    pintarContadores(datos.contadores);
    pintarListado(datos.consultas);
    pintarPaginacion();
}

function pintarContadores(contadores) {
    const tarjetas = [
        { nombre: 'Total', filtro: '' },
        ...CATEGORIAS.map(c => ({ nombre: c.nombre, filtro: c.nombre })),
    ];

    cajaContadores.innerHTML = tarjetas.map(t => `
        <button class="contador ${t.filtro === categoriaFiltro ? 'activo' : ''}" data-filtro="${t.filtro}">
            <span class="numero">${contadores[t.nombre] ?? 0}</span>
            <span class="nombre">${t.nombre}</span>
        </button>`).join('');
}

function pintarListado(consultas) {
    if (consultas.length === 0) {
        listado.innerHTML = '<tr><td colspan="5">No hay consultas en esta categoría.</td></tr>';
        return;
    }

    listado.innerHTML = consultas.map(c => {
        let categoria = c.categoria;
        if (c.estado === 'pendiente') categoria = 'Pendiente';
        if (c.estado === 'error') categoria = 'Error al clasificar';

        const tiempo = c.tiempo_ms ? `${(c.tiempo_ms / 1000).toFixed(1)} s` : '—';

        return `
            <tr>
                <td class="secundario">${formatearFecha(c.fecha)}</td>
                <td>${escaparHTML(c.texto)}</td>
                <td><span class="etiqueta ${claseCategoria(c.categoria)}">${categoria}</span></td>
                <td class="secundario">${escaparHTML(c.modelo ?? '—')}</td>
                <td class="secundario">${tiempo}</td>
            </tr>`;
    }).join('');
}

function pintarPaginacion() {
    infoPagina.textContent = `Página ${paginaActual} de ${totalPaginas}`;
    botonAnterior.disabled = paginaActual <= 1;
    botonSiguiente.disabled = paginaActual >= totalPaginas;
}

// Clic en un contador → filtrar por esa categoría
cajaContadores.addEventListener('click', (evento) => {
    const contador = evento.target.closest('.contador');
    if (!contador) return;
    categoriaFiltro = contador.dataset.filtro;
    paginaActual = 1;
    cargarConsultas();
});

botonAnterior.addEventListener('click', () => { paginaActual--; cargarConsultas(); });
botonSiguiente.addEventListener('click', () => { paginaActual++; cargarConsultas(); });

// ---------------------------------------------------------------------------
// Enviar una consulta nueva
// ---------------------------------------------------------------------------

function mostrarResultado(html, clase = '') {
    resultado.innerHTML = html;
    resultado.className = `resultado ${clase}`;
}

formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();

    const texto = campoTexto.value.trim();
    if (!texto) return;

    boton.disabled = true;
    boton.textContent = 'Clasificando…';
    mostrarResultado('<span class="detalle">La IA está analizando la consulta…</span>');

    try {
        const respuesta = await fetch(API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ texto }),
        });
        const datos = await respuesta.json();

        if (!respuesta.ok) {
            mostrarResultado(escaparHTML(datos.error), 'error');
            return;
        }

        const c = datos.consulta;
        if (c.estado === 'error') {
            mostrarResultado('La consulta se ha guardado, pero la IA no ha podido clasificarla.', 'error');
        } else {
            mostrarResultado(
                `<span class="categoria-grande">${escaparHTML(c.categoria)}</span>
                 <span class="detalle">Clasificada por ${escaparHTML(c.modelo)} en ${(c.tiempo_ms / 1000).toFixed(1)} s</span>`,
                claseCategoria(c.categoria)
            );
        }

        // Volver a la primera página sin filtro para ver la consulta nueva arriba
        campoTexto.value = '';
        categoriaFiltro = '';
        paginaActual = 1;
        await cargarConsultas();
    } catch (error) {
        mostrarResultado('No se ha podido conectar con el servidor.', 'error');
    } finally {
        boton.disabled = false;
        boton.textContent = 'Enviar';
    }
});

// Carga inicial
cargarConsultas();
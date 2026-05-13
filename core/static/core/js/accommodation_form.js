document.addEventListener('DOMContentLoaded', () => {
    const disabilityField = document.getElementById('id_disability');
    const guidelinesContainer = document.getElementById('guidelines-container');

    if (!disabilityField || !guidelinesContainer) {
        return;
    }

    const loadGuidelines = async (disabilityId) => {
        if (!disabilityId) {
            guidelinesContainer.innerHTML = '<p class="text-muted">Smjernice će se prikazati ovdje.</p>';
            return;
        }

        try {
            const response = await fetch(`/api/guidelines/?disability=${disabilityId}`);
            if (!response.ok) {
                throw new Error('Greška pri dohvaćanju smjernica.');
            }
            const data = await response.json();

            if (data.guidelines.length === 0) {
                guidelinesContainer.innerHTML = '<p class="text-muted">Nema smjernica za odabranu vrstu teškoće.</p>';
                return;
            }

            const html = data.guidelines.map(g => `
                <div class="mb-3 pb-3 border-bottom">
                    <h6>${g.title}</h6>
                    <p class="small mb-0">${g.content}</p>
                </div>
            `).join('');

            guidelinesContainer.innerHTML = html;
        } catch (error) {
            guidelinesContainer.innerHTML = '<p class="text-danger">Greška pri dohvaćanju smjernica.</p>';
        }
    };

    disabilityField.addEventListener('change', (e) => {
        loadGuidelines(e.target.value);
    });

    // Load on initial page load if disability is preselected
    if (disabilityField.value) {
        loadGuidelines(disabilityField.value);
    }
});
<?php
/**
 * Snippet « Diagnostic jardin - page Mon projet jardin » (Code Snippets, front-end).
 * Shortcode [cg_projet_jardin] : affiche le projet du client (lien /mon-projet-jardin/?projet=XXXX)
 * entre l'en-tête et le pied de page du site. Le contenu vient du service Diagnostic jardin (Cloud Run).
 */
if (!defined('CG_DIAG_API')) define('CG_DIAG_API', 'https://diagnostic-jardin-473773825833.europe-west1.run.app');

function cg_projet_jardin_id() {
    $id = isset($_GET['projet']) ? sanitize_text_field(wp_unslash($_GET['projet'])) : '';
    return preg_match('/^[0-9]{4}-[A-Za-z0-9_-]{8,20}$/', $id) ? $id : '';
}

function cg_projet_jardin_est_la_page() {
    return is_singular() && has_shortcode((string) get_post_field('post_content', get_queried_object_id()), 'cg_projet_jardin');
}

// Page personnelle : jamais en cache, jamais indexée
add_action('template_redirect', function () {
    if (!cg_projet_jardin_est_la_page()) return;
    if (!defined('DONOTCACHEPAGE')) define('DONOTCACHEPAGE', true);   // WP Rocket
    nocache_headers();
    header('Cache-Control: private, no-store, max-age=0');              // Cloudflare / Rocket CDN
    header('X-Robots-Tag: noindex, nofollow', true);
});
add_filter('wp_robots', function ($r) {
    if (cg_projet_jardin_est_la_page()) { $r['noindex'] = true; $r['nofollow'] = true; }
    return $r;
});

add_filter('rank_math/frontend/robots', function ($r) {
    if (cg_projet_jardin_est_la_page()) { $r['index'] = 'noindex'; $r['follow'] = 'nofollow'; }
    return $r;
});

// La page est en gabarit Elementor Canvas, comme les autres pages du site : on y met l'en-tête charte v2 et le pied de page (modèle 1545)
function cg_projet_jardin_cadre($html) {
    $hdr = (function_exists('cg_hdr_enabled') && cg_hdr_enabled() && function_exists('cg_hdr_render')) ? cg_hdr_render() : '';
    return $hdr . $html . do_shortcode('[elementor-template id="1545"]');
}

add_shortcode('cg_projet_jardin', function () {
    $id = cg_projet_jardin_id();
    $boite = function ($titre, $texte, $rafraichir = false) {
        $b = '<div style="max-width:640px;margin:48px auto;padding:0 16px;font-family:Roboto,Arial,sans-serif;color:#1E211F">'
            . '<h1 style="font-weight:800;font-size:32px;line-height:1.15;margin:0 0 12px">' . esc_html($titre) . '<span style="color:#EB5A00">.</span></h1>'
            . '<p style="font-size:16px;line-height:1.6;color:#5B625E;margin:0">' . esc_html($texte) . '</p>'
            . ($rafraichir ? '<script>setTimeout(function(){location.reload()},8000)</script>' : '') . '</div>';
        return cg_projet_jardin_cadre($b);
    };
    if (!$id) return $boite('Votre projet jardin', "Ce lien n'est pas complet. Ouvrez le lien reçu par email pour retrouver votre projet.");
    $r = wp_remote_get(CG_DIAG_API . '/fragment/' . rawurlencode($id), array('timeout' => 20));
    if (is_wp_error($r)) return $boite('Votre projet jardin', 'Votre projet est momentanément indisponible. Réessayez dans quelques minutes.');
    $code = wp_remote_retrieve_response_code($r);
    if ($code === 202) return $boite('Votre projet se prépare', 'Nous calculons le soleil de votre jardin et préparons votre idée d\'aménagement avec nos produits. Cela prend environ deux minutes, cette page se met à jour toute seule.', true);
    if ($code !== 200) return $boite('Projet introuvable', "Ce projet n'existe pas ou a expiré. Vous pouvez refaire votre diagnostic en deux minutes.");
    return cg_projet_jardin_cadre(wp_remote_retrieve_body($r));   // contenu produit par notre service (styles préfixés .cgp)
});

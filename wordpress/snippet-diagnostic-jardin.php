<?php
/**
 * Snippet « Diagnostic jardin - questionnaire » (Code Snippets, front-end).
 * Shortcode [cg_diagnostic_jardin] : questionnaire du diagnostic gratuit, servi par le service Diagnostic jardin (Cloud Run).
 * Le lien du projet envoyé au client pointe vers la page « Mon projet jardin » (shortcode [cg_projet_jardin]).
 * Page en gabarit Elementor Canvas : l'en-tête et le pied de page sont ajoutés ici, comme pour « Mon projet jardin ».
 */
if (!defined('CG_DIAG_API')) define('CG_DIAG_API', 'https://diagnostic-jardin-349938922301.europe-west1.run.app');
if (!defined('CG_DIAG_PAGE_PROJET')) define('CG_DIAG_PAGE_PROJET', '/mon-projet-jardin/?projet=');

function cg_diag_est_la_page() {
    return is_singular() && has_shortcode((string) get_post_field('post_content', get_queried_object_id()), 'cg_diagnostic_jardin');
}

// Le questionnaire garde la saisie du client dans son navigateur : la page ne doit pas être servie depuis un cache partagé
add_action('template_redirect', function () {
    if (!cg_diag_est_la_page()) return;
    if (!defined('DONOTCACHEPAGE')) define('DONOTCACHEPAGE', true);   // WP Rocket
});

// Le script du questionnaire ne doit être ni retardé ni regroupé par WP Rocket
add_filter('rocket_delay_js_exclusions', function ($l) { $l[] = 'run.app/q/q.js'; return $l; });
add_filter('rocket_exclude_js', function ($l) { $l[] = '(.*)run.app/q/q.js'; return $l; });

add_shortcode('cg_diagnostic_jardin', function () {
    $html = '<div class="cgq-hero" style="max-width:640px;margin:0 auto;padding:32px 16px 0;font-family:Roboto,Arial,sans-serif;color:#1E211F">'
        . '<h1 style="font-weight:800;font-size:clamp(30px,6vw,44px);line-height:1.12;margin:0;letter-spacing:-.01em">Le diagnostic gratuit de votre <span style="color:#049E00">jardin</span><span style="color:#EB5A00">.</span></h1></div>'
        . '<div id="cg-diag" data-api="' . esc_attr(CG_DIAG_API) . '" data-projet="' . esc_attr(CG_DIAG_PAGE_PROJET) . '"></div>'
        . '<script src="' . esc_url(CG_DIAG_API . '/q/q.js') . '" defer data-no-optimize="1" data-cfasync="false"></script>';
    $hdr = (function_exists('cg_hdr_enabled') && cg_hdr_enabled() && function_exists('cg_hdr_render')) ? cg_hdr_render() : '';
    return $hdr . $html . do_shortcode('[elementor-template id="1545"]');
});

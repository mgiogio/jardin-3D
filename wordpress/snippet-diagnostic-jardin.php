<?php
/**
 * Snippet « Diagnostic jardin - questionnaire » (Code Snippets, front-end).
 * Shortcode [cg_diagnostic_jardin] : questionnaire du diagnostic gratuit, servi par le service Diagnostic jardin (Cloud Run).
 * Le lien du projet envoyé au client pointe vers la page « Mon projet jardin » (shortcode [cg_projet_jardin]).
 * Page en gabarit Elementor Canvas : l'en-tête et le pied de page sont ajoutés ici, comme pour « Mon projet jardin ».
 */
if (!defined('CG_DIAG_API')) define('CG_DIAG_API', 'https://diagnostic-jardin-349938922301.europe-west1.run.app');

// Lien vers la page « Mon projet jardin » : on retrouve la page qui contient [cg_projet_jardin] (brouillon compris, pour le staging)
function cg_diag_page_projet() {
    $u = get_transient('cg_diag_page_projet');
    if ($u) return $u;
    $p = get_posts(array('post_type' => 'page', 'post_status' => array('publish', 'draft', 'private'), 's' => '[cg_projet_jardin', 'numberposts' => 1, 'fields' => 'ids'));
    $u = $p ? get_permalink($p[0]) : home_url('/mon-projet-jardin/');
    $u .= (strpos($u, '?') === false ? '?' : '&') . 'projet=';
    set_transient('cg_diag_page_projet', $u, HOUR_IN_SECONDS);
    return $u;
}

// Contenu sous le questionnaire (ce que l'on reçoit, plantes, FAQ) : rendu par le service, gardé 10 minutes
function cg_diag_contenu() {
    $h = get_transient('cg_diag_lp');
    if ($h !== false) return $h;
    $r = wp_remote_get(CG_DIAG_API . '/lp', array('timeout' => 15));
    if (is_wp_error($r) || wp_remote_retrieve_response_code($r) !== 200) return '';
    $h = wp_remote_retrieve_body($r);
    set_transient('cg_diag_lp', $h, 10 * MINUTE_IN_SECONDS);
    return $h;
}

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
add_filter('rocket_exclude_inline_js', function ($l) { $l[] = 'cglp-liste'; return $l; });
add_filter('rocket_delay_js_exclusions', function ($l) { $l[] = 'cglp-liste'; return $l; });

add_shortcode('cg_diagnostic_jardin', function () {
    $html = '<div class="cgq-hero" style="max-width:640px;margin:0 auto;padding:32px 16px 0;font-family:Roboto,Arial,sans-serif;color:#1E211F">'
        . '<h1 style="font-weight:800;font-size:clamp(30px,6vw,44px);line-height:1.12;margin:0;letter-spacing:-.01em">Le diagnostic gratuit de votre <span style="color:#049E00">jardin</span><span style="color:#EB5A00">.</span></h1></div>'
        . '<div id="cg-diag" data-api="' . esc_attr(CG_DIAG_API) . '" data-projet="' . esc_attr(cg_diag_page_projet()) . '"></div>'
        . '<script src="' . esc_url(CG_DIAG_API . '/q/q.js') . '" defer data-no-optimize="1" data-cfasync="false"></script>'
        . cg_diag_contenu();   // contenu produit par notre service (styles préfixés .cglp)
    $hdr = (function_exists('cg_hdr_enabled') && cg_hdr_enabled() && function_exists('cg_hdr_render')) ? cg_hdr_render() : '';
    return $hdr . $html . do_shortcode('[elementor-template id="1545"]');
});

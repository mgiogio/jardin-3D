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

// Page d'entrée au-dessus du questionnaire (titre, visuel, bouton « Je commence ») : rendue par le service.
// Copie fraîche 10 minutes, et une copie de secours gardée sans limite : si le service met du temps à répondre (démarrage à froid),
// la page affiche la dernière copie ; s'il n'y en a aucune, le navigateur va la chercher lui-même.
function cg_diag_contenu() {
    $h = get_transient('cg_diag_lp2');
    if ($h !== false && $h !== '') return $h;
    $r = wp_remote_get(CG_DIAG_API . '/lp', array('timeout' => 25));
    if (!is_wp_error($r) && wp_remote_retrieve_response_code($r) === 200 && strpos(wp_remote_retrieve_body($r), 'cglp') !== false) {
        $h = wp_remote_retrieve_body($r);
        set_transient('cg_diag_lp2', $h, 10 * MINUTE_IN_SECONDS);
        update_option('cg_diag_lp2_secours', $h, false);
        return $h;
    }
    $h = get_option('cg_diag_lp2_secours');
    if ($h) return $h;
    return '<div id="cglp-auto"></div><script>(function(){var d=document.getElementById("cglp-auto");fetch(' . wp_json_encode(CG_DIAG_API . '/lp') . ').then(function(r){return r.text()}).then(function(t){d.innerHTML=t;'
        . '[].forEach.call(d.querySelectorAll("script"),function(o){var n=document.createElement("script");n.textContent=o.textContent;o.replaceWith(n)})}).catch(function(){})})()</script>';
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
add_filter('rocket_exclude_inline_js', function ($l) { $l[] = 'cglp-auto'; return $l; });
add_filter('rocket_delay_js_exclusions', function ($l) { $l[] = 'cglp-auto'; return $l; });

add_shortcode('cg_diagnostic_jardin', function () {
    // page d'entrée (titre, visuel, bouton « Je commence ») produite par notre service, puis le questionnaire, caché jusqu'au clic
    $html = '<div style="background:#F4F6F7">' . cg_diag_contenu() . '</div>'
        . '<div id="cg-diag" data-api="' . esc_attr(CG_DIAG_API) . '" data-projet="' . esc_attr(cg_diag_page_projet()) . '"></div>'
        . '<script src="' . esc_url(CG_DIAG_API . '/q/q.js') . '" defer data-no-optimize="1" data-cfasync="false"></script>';
    $hdr = (function_exists('cg_hdr_enabled') && cg_hdr_enabled() && function_exists('cg_hdr_render')) ? cg_hdr_render() : '';
    return $hdr . $html . do_shortcode('[elementor-template id="1545"]');
});

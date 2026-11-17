<?php
/*
 * Diagnostic jardin - bloc sur la page d'accueil
 * Un encart « Le diagnostic gratuit de votre jardin » posé sur l'accueil, juste avant les blocs produits
 * (après la bande « Déjà des milliers de kits posés »). Le bloc est écrit en bas de page puis déplacé à sa place :
 * aucune modification de la page Elementor. Si la section repère n'existe plus (nouvelle page d'accueil), il reste caché.
 * Le style porte un id contenant « cg-cta » pour que le CSS utilisé de WP Rocket le garde (voir snippet 59).
 */
add_action( 'wp_footer', function () {
	if ( ! is_front_page() ) {
		return;
	}
	$img  = 'https://cover.green/wp-content/uploads/2026/11/diagnostic-';
	$lien = home_url( '/diagnostic/?utm_source=cover.green&utm_medium=bloc-accueil&utm_campaign=diagnostic-jardin' );
	?>
<style id="cg-cta-diag-accueil">
.cgda{display:none;max-width:1200px;margin:48px auto;padding:0 20px;box-sizing:border-box;font-family:Roboto,Arial,sans-serif}
.cgda.cgda-ok{display:block}
.cgda a.cgda-carte{display:flex;flex-wrap:wrap;background:#EAF7E5;border-radius:16px;overflow:hidden;text-decoration:none;color:#1E211F}
.cgda .cgda-photo{position:relative;flex:1 1 420px;min-height:300px;overflow:hidden}
.cgda .cgda-photo img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}
.cgda .cgda-photo img.cgda-ap{opacity:0;animation:cgda-fondu 9s ease-in-out infinite}
.cgda .cgda-tag{position:absolute;left:16px;bottom:16px;padding:6px 11px;border-radius:7px;font-size:13px;font-weight:700;color:#fff;background:rgba(30,33,31,.72)}
.cgda .cgda-tag.cgda-ap{opacity:0;background:#049E00;animation:cgda-fondu 9s ease-in-out infinite}
.cgda .cgda-tag.cgda-av{animation:cgda-fondu-inv 9s ease-in-out infinite}
@keyframes cgda-fondu{0%,8%{opacity:0}17%,90%{opacity:1}100%{opacity:0}}
@keyframes cgda-fondu-inv{0%,8%{opacity:1}17%,90%{opacity:0}100%{opacity:1}}
@media (prefers-reduced-motion:reduce){.cgda .cgda-ap{animation:none!important;opacity:1!important}.cgda .cgda-tag.cgda-av{display:none}}
.cgda .cgda-texte{flex:1 1 380px;padding:36px 36px 38px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:14px}
.cgda .cgda-nouveau{font-size:14px;font-weight:700;color:#049E00}
.cgda h2{margin:0;font-size:clamp(26px,3vw,36px);line-height:1.15;font-weight:800;color:#1E211F}
.cgda h2 span{color:#049E00}
.cgda p{margin:0;font-size:17px;line-height:1.5;color:#4B5258;max-width:470px}
.cgda .cgda-cta{display:inline-flex;align-items:center;justify-content:center;min-width:200px;height:56px;padding:0 24px;box-sizing:border-box;border:1px solid #EB5A00;border-radius:8px;background:#EB5A00;color:#fff;font-size:16px;font-weight:600;margin-top:6px}
.cgda a.cgda-carte:hover .cgda-cta{background:#C84800;border-color:#C84800}
@media (max-width:767px){.cgda{margin:32px auto;padding:0 16px}.cgda .cgda-photo{min-height:220px}.cgda .cgda-texte{padding:24px 20px 26px}.cgda .cgda-cta{width:100%}}
</style>
<section class="cgda" id="cg-diag-accueil" aria-label="Diagnostic jardin gratuit">
	<a class="cgda-carte" href="<?php echo esc_url( $lien ); ?>" data-cg-diag="accueil">
		<div class="cgda-photo">
			<img class="cgda-av" src="<?php echo esc_url( $img . 'jardin-avant.webp' ); ?>" width="1200" height="815" alt="Un jardin avant : pelouse et terrasse derrière la maison" loading="lazy" decoding="async">
			<img class="cgda-ap" src="<?php echo esc_url( $img . 'jardin-apres.webp' ); ?>" width="1200" height="815" alt="Le même jardin imaginé par notre outil : terrasse bois, pergola, clôture et massifs" loading="lazy" decoding="async">
			<span class="cgda-tag cgda-av">Avant</span><span class="cgda-tag cgda-ap">Après, imaginé par notre outil</span>
		</div>
		<div class="cgda-texte">
			<span class="cgda-nouveau">Nouveau</span>
			<h2>Le diagnostic gratuit de votre <span>jardin</span></h2>
			<p>Quoi planter et quand, où créer de l'ombre et de l'intimité, et ce que coûte chaque idée. Il suffit de votre adresse : tout arrive par email en 3 minutes.</p>
			<span class="cgda-cta">Faire mon diagnostic</span>
		</div>
	</a>
</section>
<script>
(function () {
	var b = document.getElementById('cg-diag-accueil'); if (!b) return;
	var repere = document.querySelector('[data-elementor-id="58"] > [data-id="cac90ab"]');
	if (!repere) return;                                   // page d'accueil changée : le bloc reste caché
	repere.parentNode.insertBefore(b, repere); b.classList.add('cgda-ok');
	b.querySelector('a').addEventListener('click', function () { try { window.dataLayer = window.dataLayer || []; dataLayer.push({ event: 'cgp_accueil_diagnostic' }); } catch (e) {} });
})();
</script>
	<?php
}, 20 );

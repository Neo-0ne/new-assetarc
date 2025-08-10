
<?php
/**
 * Plugin Name: AssetArc SSO (Email OTP)
 * Description: Login modal talking to the Auth Gateway. Provides [assetarc_login].
 * Version: 1.1.0
 * Author: AssetArc
 */
if (!defined('ABSPATH')) exit;
if (!defined('ASSETARC_AUTH_BASE')) define('ASSETARC_AUTH_BASE', 'https://auth.asset-arc.com');

add_action('wp_enqueue_scripts', function() {
  wp_enqueue_script('assetarc-sso', plugins_url('assets/sso.js', __FILE__), [], '1.1.0', true);
  wp_localize_script('assetarc-sso', 'ASSETARC_SSO', ['authBase'=>ASSETARC_AUTH_BASE]);
});

function assetarc_login_shortcode(){ ob_start(); include __DIR__.'/templates/login-modal.php'; return ob_get_clean(); }
add_shortcode('assetarc_login','assetarc_login_shortcode');

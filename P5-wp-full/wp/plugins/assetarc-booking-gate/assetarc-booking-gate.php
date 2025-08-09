
<?php
/**
 * Plugin Name: AssetArc Booking Gate
 * Description: Shows availability, requires payment, then reveals Calendly embed. Shortcode: [assetarc_booking_gate]
 * Version: 1.2.0
 * Author: AssetArc
 */
if (!defined('ABSPATH')) exit;

if (!defined('ASSETARC_GATEWAY_BASE')) define('ASSETARC_GATEWAY_BASE', 'https://api.asset-arc.com');
if (!defined('ASSETARC_CALENDLY_URL')) define('ASSETARC_CALENDLY_URL', 'https://calendly.com/your-org/consult');

add_action('wp_enqueue_scripts', function(){
  wp_enqueue_script('assetarc-gate', plugins_url('assets/gate.js', __FILE__), [], '1.2.0', true);
  wp_localize_script('assetarc-gate', 'ASSETARC_GATE', [
    'base'=>ASSETARC_GATEWAY_BASE,
    'calendly'=>ASSETARC_CALENDLY_URL
  ]);
});

function assetarc_booking_gate_shortcode($atts=[]){
  ob_start(); include __DIR__ . '/templates/booking-gate.php'; return ob_get_clean();
}
add_shortcode('assetarc_booking_gate', 'assetarc_booking_gate_shortcode');

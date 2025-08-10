
<?php
add_action('wp_enqueue_scripts', function(){
  wp_enqueue_style('assetarc-style', get_stylesheet_uri(), [], '1.1.0');
});

<?php
/**
 * Plugin Name:       Flavor Pairing Graph
 * Plugin URI:        https://example.com/flavor-pairing-graph
 * Description:       Explore ingredient relationships through a graph-powered flavor pairing assistant.
 * Version:           0.1.0
 * Author:            Flavor Pairing Team
 * Author URI:        https://example.com
 * License:           GPL-2.0-or-later
 * License URI:       http://www.gnu.org/licenses/gpl-2.0.txt
 * Text Domain:       flavor-pairing
 *
 * @package Flavor_Pairing
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit; // Exit if accessed directly.
}

if ( ! defined( 'FLAVOR_PAIRING_VERSION' ) ) {
	define( 'FLAVOR_PAIRING_VERSION', '0.1.0' );
}

if ( ! defined( 'FLAVOR_PAIRING_PLUGIN_DIR' ) ) {
	define( 'FLAVOR_PAIRING_PLUGIN_DIR', plugin_dir_path( __FILE__ ) );
}

if ( ! defined( 'FLAVOR_PAIRING_PLUGIN_URL' ) ) {
	define( 'FLAVOR_PAIRING_PLUGIN_URL', plugin_dir_url( __FILE__ ) );
}

/**
 * Autoloader for Flavor Pairing classes.
 *
 * @param string $class_name Fully-qualified class name.
 */
function flavor_pairing_autoload( $class_name ) {
	if ( false === strpos( $class_name, 'Flavor_Pairing' ) ) {
		return;
	}

	$relative_class = strtolower( str_replace( '_', '-', $class_name ) );
	$paths          = array(
		'includes/class-' . $relative_class . '.php',
		'admin/class-' . $relative_class . '.php',
		'public/class-' . $relative_class . '.php',
	);

	foreach ( $paths as $path ) {
		$file = FLAVOR_PAIRING_PLUGIN_DIR . $path;
		if ( file_exists( $file ) ) {
			require_once $file;
			return;
		}
	}
}

spl_autoload_register( 'flavor_pairing_autoload' );

/**
 * Initialize plugin core.
 */
function flavor_pairing_run() {
	$plugin = new Flavor_Pairing();
	$plugin->run();
}

register_activation_hook( __FILE__, array( 'Flavor_Pairing', 'activate' ) );
register_deactivation_hook( __FILE__, array( 'Flavor_Pairing', 'deactivate' ) );

add_action( 'plugins_loaded', 'flavor_pairing_run' );

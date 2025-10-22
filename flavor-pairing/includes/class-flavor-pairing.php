<?php
/**
 * Core plugin class.
 *
 * @package Flavor_Pairing
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Class Flavor_Pairing
 *
 * Coordinates admin, public, and data layers.
 */
class Flavor_Pairing {

	/**
	 * Admin instance.
	 *
	 * @var Flavor_Pairing_Admin
	 */
	protected $admin;

	/**
	 * Public instance.
	 *
	 * @var Flavor_Pairing_Public
	 */
	protected $public;

	/**
	 * Graph adapter.
	 *
	 * @var Flavor_Pairing_Graph_Adapter
	 */
	protected $graph_adapter;

	/**
	 * Post types registrar.
	 *
	 * @var Flavor_Pairing_Post_Types
	 */
	protected $post_types;

	/**
	 * Constructor.
	 */
	public function __construct() {
		$this->set_locale();
		$this->load_dependencies();
		$this->define_admin_hooks();
		$this->define_public_hooks();
	}

	/**
	 * Runs during plugin activation.
	 */
	public static function activate() {
		$post_types = new Flavor_Pairing_Post_Types();
		$post_types->register();
		flush_rewrite_rules();
	}

	/**
	 * Runs during plugin deactivation.
	 */
	public static function deactivate() {
		flush_rewrite_rules();
	}

	/**
	 * Load plugin text domain.
	 */
	private function set_locale() {
		add_action(
			'plugins_loaded',
			function () {
				load_plugin_textdomain( 'flavor-pairing', false, basename( dirname( __DIR__ ) ) . '/languages/' );
			}
		);
	}

	/**
	 * Load primary dependencies.
	 */
	private function load_dependencies() {
		$this->graph_adapter = new Flavor_Pairing_Graph_Adapter();
		$this->post_types    = new Flavor_Pairing_Post_Types();
		$this->admin         = new Flavor_Pairing_Admin( $this->graph_adapter );
		$this->public        = new Flavor_Pairing_Public( $this->graph_adapter );
	}

	/**
	 * Register admin hooks.
	 */
	private function define_admin_hooks() {
		add_action( 'init', array( $this->post_types, 'register' ) );
		add_action( 'admin_enqueue_scripts', array( $this->admin, 'enqueue_styles' ) );
		add_action( 'admin_enqueue_scripts', array( $this->admin, 'enqueue_scripts' ) );
		add_action( 'add_meta_boxes', array( $this->admin, 'register_meta_boxes' ) );
		add_action( 'save_post', array( $this->admin, 'save_post_meta' ), 10, 2 );
	}

	/**
	 * Register public-facing hooks.
	 */
	private function define_public_hooks() {
		add_action( 'wp_enqueue_scripts', array( $this->public, 'enqueue_styles' ) );
		add_action( 'wp_enqueue_scripts', array( $this->public, 'enqueue_scripts' ) );
		add_shortcode( 'flavor_pairings', array( $this->public, 'render_pairings_shortcode' ) );
	}

	/**
	 * Bootstrap plugin.
	 */
	public function run() {
		// Intentionally left minimal; hooks are registered during construction.
	}
}

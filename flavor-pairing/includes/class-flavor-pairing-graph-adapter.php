<?php
/**
 * Graph database adapter abstraction.
 *
 * @package Flavor_Pairing
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Class Flavor_Pairing_Graph_Adapter
 *
 * Provides a seam between WordPress and the chosen graph database service.
 */
class Flavor_Pairing_Graph_Adapter {

	/**
	 * Placeholder for connection settings.
	 *
	 * @var array
	 */
	private $settings = array();

	/**
	 * Inject settings if already stored.
	 */
	public function __construct() {
		$this->settings = get_option(
			'flavor_pairing_graph_settings',
			array(
				'endpoint' => '',
				'token'    => '',
				'vendor'   => 'neo4j',
			)
		);
	}

	/**
	 * Retrieve settings.
	 *
	 * @return array
	 */
	public function get_settings() {
		return $this->settings;
	}

	/**
	 * Persist new settings.
	 *
	 * @param array $settings Graph configuration.
	 */
	public function update_settings( $settings ) {
		$this->settings = wp_parse_args(
			$settings,
			array(
				'endpoint' => '',
				'token'    => '',
				'vendor'   => 'neo4j',
			)
		);

		update_option( 'flavor_pairing_graph_settings', $this->settings );
	}

	/**
	 * Stubbed query runner.
	 *
	 * @param string $query Query string.
	 * @param array  $params Optional parameters.
	 *
	 * @return array
	 */
	public function run_query( $query, $params = array() ) {
		// @todo Replace with vendor-specific client implementation.
		return array(
			'query'  => $query,
			'params' => $params,
			'data'   => array(),
		);
	}

	/**
	 * Prepare node payload for a given WP ingredient object.
	 *
	 * @param WP_Post $post Ingredient post.
	 *
	 * @return array<string, mixed>
	 */
	public function map_ingredient_node( $post ) {
		return array(
			'id'          => $post->ID,
			'name'        => get_the_title( $post ),
			'flavor_note' => get_post_meta( $post->ID, '_flavor_pairing_notes', true ),
			'seasonality' => get_post_meta( $post->ID, '_flavor_pairing_seasonality', true ),
			'source'      => 'wordpress',
		);
	}
}

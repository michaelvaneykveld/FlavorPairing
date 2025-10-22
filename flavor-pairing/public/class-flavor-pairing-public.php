<?php
/**
 * Public-facing functionality.
 *
 * @package Flavor_Pairing
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Class Flavor_Pairing_Public
 */
class Flavor_Pairing_Public {

	/**
	 * Graph adapter.
	 *
	 * @var Flavor_Pairing_Graph_Adapter
	 */
	protected $graph_adapter;

	/**
	 * Constructor.
	 *
	 * @param Flavor_Pairing_Graph_Adapter $graph_adapter Graph adapter.
	 */
	public function __construct( Flavor_Pairing_Graph_Adapter $graph_adapter ) {
		$this->graph_adapter = $graph_adapter;
	}

	/**
	 * Enqueue public styles.
	 */
	public function enqueue_styles() {
		wp_enqueue_style(
			'flavor-pairing-public',
			FLAVOR_PAIRING_PLUGIN_URL . 'assets/css/public.css',
			array(),
			FLAVOR_PAIRING_VERSION
		);
	}

	/**
	 * Enqueue public scripts.
	 */
	public function enqueue_scripts() {
		wp_enqueue_script(
			'flavor-pairing-public',
			FLAVOR_PAIRING_PLUGIN_URL . 'assets/js/public.js',
			array( 'wp-element' ),
			FLAVOR_PAIRING_VERSION,
			true
		);

		wp_localize_script(
			'flavor-pairing-public',
			'FlavorPairingPublic',
			array(
				'endpoint' => rest_url( 'flavor-pairing/v1' ),
				'nonce'    => wp_create_nonce( 'wp_rest' ),
			)
		);
	}

	/**
	 * Shortcode renderer: [flavor_pairings ingredient="vanilla"].
	 *
	 * @param array $atts Shortcode attributes.
	 *
	 * @return string
	 */
	public function render_pairings_shortcode( $atts ) {
		$atts = shortcode_atts(
			array(
				'ingredient' => '',
			),
			$atts,
			'flavor_pairings'
		);

		$ingredient = sanitize_text_field( $atts['ingredient'] );

		if ( empty( $ingredient ) ) {
			return '<p>' . esc_html__( 'Provide an ingredient to display pairings.', 'flavor-pairing' ) . '</p>';
		}

		$response = $this->graph_adapter->run_query(
			'MATCH (i:Ingredient {name: $name})-[:PAIRS_WITH]->(pairing) RETURN pairing LIMIT 10',
			array(
				'name' => $ingredient,
			)
		);

		if ( empty( $response['data'] ) ) {
			return '<p>' . esc_html__( 'No pairings found yet. Try another ingredient.', 'flavor-pairing' ) . '</p>';
		}

		$output = '<ul class="flavor-pairing-list">';

		foreach ( $response['data'] as $node ) {
			$name = isset( $node['name'] ) ? $node['name'] : __( 'Unknown', 'flavor-pairing' );
			$output .= '<li>' . esc_html( $name ) . '</li>';
		}

		$output .= '</ul>';

		return $output;
	}
}

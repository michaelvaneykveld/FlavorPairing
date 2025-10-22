<?php
/**
 * Registers custom post types and taxonomies.
 *
 * @package Flavor_Pairing
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Class Flavor_Pairing_Post_Types
 */
class Flavor_Pairing_Post_Types {

	/**
	 * Register post types and taxonomies.
	 */
	public function register() {
		$this->register_ingredient_post_type();
		$this->register_flavor_taxonomy();
		$this->register_technique_taxonomy();
	}

	/**
	 * Registers the ingredient post type.
	 */
	private function register_ingredient_post_type() {
		$labels = array(
			'name'               => __( 'Ingredients', 'flavor-pairing' ),
			'singular_name'      => __( 'Ingredient', 'flavor-pairing' ),
			'add_new'            => __( 'Add Ingredient', 'flavor-pairing' ),
			'add_new_item'       => __( 'Add New Ingredient', 'flavor-pairing' ),
			'edit_item'          => __( 'Edit Ingredient', 'flavor-pairing' ),
			'new_item'           => __( 'New Ingredient', 'flavor-pairing' ),
			'all_items'          => __( 'All Ingredients', 'flavor-pairing' ),
			'view_item'          => __( 'View Ingredient', 'flavor-pairing' ),
			'search_items'       => __( 'Search Ingredients', 'flavor-pairing' ),
			'not_found'          => __( 'No ingredients found', 'flavor-pairing' ),
			'not_found_in_trash' => __( 'No ingredients found in Trash', 'flavor-pairing' ),
			'menu_name'          => __( 'Ingredients', 'flavor-pairing' ),
		);

		$args = array(
			'labels'             => $labels,
			'public'             => true,
			'show_in_rest'       => true,
			'supports'           => array( 'title', 'editor', 'thumbnail', 'excerpt' ),
			'menu_icon'          => 'dashicons-carrot',
			'has_archive'        => true,
			'rewrite'            => array( 'slug' => 'ingredients' ),
			'show_in_graphql'    => true,
			'graphql_single_name'=> 'ingredient',
			'graphql_plural_name'=> 'ingredients',
		);

		register_post_type( 'flavor_ingredient', $args );
	}

	/**
	 * Register taxonomy for flavor families.
	 */
	private function register_flavor_taxonomy() {
		$labels = array(
			'name'          => __( 'Flavor Families', 'flavor-pairing' ),
			'singular_name' => __( 'Flavor Family', 'flavor-pairing' ),
			'search_items'  => __( 'Search Flavor Families', 'flavor-pairing' ),
			'all_items'     => __( 'All Flavor Families', 'flavor-pairing' ),
			'edit_item'     => __( 'Edit Flavor Family', 'flavor-pairing' ),
			'update_item'   => __( 'Update Flavor Family', 'flavor-pairing' ),
			'add_new_item'  => __( 'Add New Flavor Family', 'flavor-pairing' ),
			'new_item_name' => __( 'New Flavor Family', 'flavor-pairing' ),
			'menu_name'     => __( 'Flavor Families', 'flavor-pairing' ),
		);

		$args = array(
			'hierarchical'      => true,
			'labels'            => $labels,
			'show_ui'           => true,
			'show_in_rest'      => true,
			'show_admin_column' => true,
			'rewrite'           => array( 'slug' => 'flavor-family' ),
		);

		register_taxonomy( 'flavor_family', array( 'flavor_ingredient' ), $args );
	}

	/**
	 * Register taxonomy for techniques or pair contexts.
	 */
	private function register_technique_taxonomy() {
		$labels = array(
			'name'          => __( 'Techniques', 'flavor-pairing' ),
			'singular_name' => __( 'Technique', 'flavor-pairing' ),
		);

		$args = array(
			'hierarchical'      => false,
			'labels'            => $labels,
			'show_ui'           => true,
			'show_in_rest'      => true,
			'show_admin_column' => true,
			'rewrite'           => array( 'slug' => 'technique' ),
		);

		register_taxonomy( 'flavor_technique', array( 'flavor_ingredient' ), $args );
	}
}

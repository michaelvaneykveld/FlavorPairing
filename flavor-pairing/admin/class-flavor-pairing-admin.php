<?php
/**
 * Admin facing functionality.
 *
 * @package Flavor_Pairing
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Class Flavor_Pairing_Admin
 */
class Flavor_Pairing_Admin {

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
	 * Enqueue admin styles.
	 */
	public function enqueue_styles() {
		wp_enqueue_style(
			'flavor-pairing-admin',
			FLAVOR_PAIRING_PLUGIN_URL . 'assets/css/admin.css',
			array(),
			FLAVOR_PAIRING_VERSION
		);
	}

	/**
	 * Enqueue admin scripts.
	 */
	public function enqueue_scripts() {
		wp_enqueue_script(
			'flavor-pairing-admin',
			FLAVOR_PAIRING_PLUGIN_URL . 'assets/js/admin.js',
			array( 'wp-api-fetch' ),
			FLAVOR_PAIRING_VERSION,
			true
		);

		wp_localize_script(
			'flavor-pairing-admin',
			'FlavorPairingAdmin',
			array(
				'nonce'    => wp_create_nonce( 'wp_rest' ),
				'settings' => $this->graph_adapter->get_settings(),
			)
		);
	}

	/**
	 * Register ingredient meta boxes.
	 */
	public function register_meta_boxes() {
		add_meta_box(
			'flavor_pairing_notes',
			__( 'Flavor Notes', 'flavor-pairing' ),
			array( $this, 'render_flavor_notes_meta_box' ),
			'flavor_ingredient',
			'normal',
			'default'
		);
	}

	/**
	 * Render the flavor notes meta box.
	 *
	 * @param WP_Post $post Current post.
	 */
	public function render_flavor_notes_meta_box( $post ) {
		wp_nonce_field( 'flavor_pairing_save_meta', 'flavor_pairing_meta_nonce' );

		$notes       = get_post_meta( $post->ID, '_flavor_pairing_notes', true );
		$seasonality = get_post_meta( $post->ID, '_flavor_pairing_seasonality', true );
		?>
		<p>
			<label for="flavor_pairing_notes">
				<?php esc_html_e( 'Flavor descriptors, intensifiers, and complementary notes.', 'flavor-pairing' ); ?>
			</label>
			<textarea
				name="flavor_pairing_notes"
				id="flavor_pairing_notes"
				class="widefat"
				rows="4"
			><?php echo esc_textarea( $notes ); ?></textarea>
		</p>
		<p>
			<label for="flavor_pairing_seasonality">
				<?php esc_html_e( 'Seasonality (e.g., spring, summer).', 'flavor-pairing' ); ?>
			</label>
			<input
				type="text"
				name="flavor_pairing_seasonality"
				id="flavor_pairing_seasonality"
				class="widefat"
				value="<?php echo esc_attr( $seasonality ); ?>"
			/>
		</p>
		<?php
	}

	/**
	 * Persist meta box data.
	 *
	 * @param int     $post_id Post ID.
	 * @param WP_Post $post    Post.
	 */
	public function save_post_meta( $post_id, $post ) {
		if ( 'flavor_ingredient' !== $post->post_type ) {
			return;
		}

		if ( ! isset( $_POST['flavor_pairing_meta_nonce'] ) || ! wp_verify_nonce( sanitize_key( wp_unslash( $_POST['flavor_pairing_meta_nonce'] ) ), 'flavor_pairing_save_meta' ) ) {
			return;
		}

		if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
			return;
		}

		if ( ! current_user_can( 'edit_post', $post_id ) ) {
			return;
		}

		$notes       = isset( $_POST['flavor_pairing_notes'] ) ? sanitize_textarea_field( wp_unslash( $_POST['flavor_pairing_notes'] ) ) : '';
		$seasonality = isset( $_POST['flavor_pairing_seasonality'] ) ? sanitize_text_field( wp_unslash( $_POST['flavor_pairing_seasonality'] ) ) : '';

		update_post_meta( $post_id, '_flavor_pairing_notes', $notes );
		update_post_meta( $post_id, '_flavor_pairing_seasonality', $seasonality );

		// Placeholder: sync ingredient node with graph database.
		$this->graph_adapter->run_query(
			'MATCH (i:Ingredient {id: $id}) RETURN i',
			array(
				'id'     => $post_id,
				'payload'=> $this->graph_adapter->map_ingredient_node( $post ),
			)
		);
	}
}

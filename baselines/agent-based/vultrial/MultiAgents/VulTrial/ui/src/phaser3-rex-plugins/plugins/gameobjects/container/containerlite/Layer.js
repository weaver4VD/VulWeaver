import GetLocalState from './utils/GetLocalState.js';

export default {
    enableLayer() {
        if (this.privateRenderLayer) {
            return this;
        }

        var layer = this.scene.add.layer();

        this.moveDepthBelow(layer);

        this.addToLayer(layer);

        this.privateRenderLayer = layer;

        return this;
    },

    getLayer() {
        if (!this.privateRenderLayer) {
            this.enableLayer();
        }

        return this.privateRenderLayer;
    },

    getRenderLayer() {
        if (this.privateRenderLayer) {
            return this.privateRenderLayer;
        }
        var parent = this.getParent();
        while (parent) {
            var layer = parent.privateRenderLayer;
            if (layer) {
                return layer;
            }
            parent = parent.getParent();
        }

        return null;
    },
    addToRenderLayer(gameObject) {
        if (!gameObject.displayList) {
            return this;
        }
        var layer = this.getRenderLayer();
        if (!layer) {
            return this;
        }

        if (gameObject.isRexContainerLite) {
            gameObject.addToLayer(layer);
        } else {
            layer.add(gameObject);
        }

        var state = GetLocalState(gameObject);
        state.layer = layer;

        return this;
    },
    removeFromRenderLayer(gameObject) {
        var state = GetLocalState(gameObject);
        var layer = state.layer;
        if (!layer) {
            return this;
        }

        layer.remove(gameObject);
        state.layer = null;

        return this;
    },
}
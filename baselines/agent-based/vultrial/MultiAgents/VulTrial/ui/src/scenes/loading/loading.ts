import { Scene } from "phaser";

export class LoadingScene extends Scene {

  constructor() {
    super("loading-scene");
  }

  preload(): void {
    this.load.baseURL = "assets/";
    this.load.spritesheet("Brendan", "sprites/brendan.png", {
      frameWidth: 14,
      frameHeight: 21,
    });

    this.load.spritesheet("May", "sprites/may.png", {
      frameWidth: 14,
      frameHeight: 20,
    });

    this.load.spritesheet("Birch", "sprites/birch.png", {
      frameWidth: 16,
      frameHeight: 20,
    });

    this.load.spritesheet("Steven", "sprites/steven.png", {
      frameWidth: 16,
      frameHeight: 21,
    });

    this.load.spritesheet("Maxie", "sprites/maxie.png", {
      frameWidth: 16,
      frameHeight: 20,
    });

    this.load.spritesheet("Archie", "sprites/archie.png", {
      frameWidth: 16,
      frameHeight: 20,
    });

    this.load.spritesheet("Joseph", "sprites/joseph.png", {
      frameWidth: 14,
      frameHeight: 21,
    });
    this.load.image({
      key: "tiles",
      url: "tilemaps/tiles/tileset.png",
    });
    this.load.tilemapTiledJSON("town", "tilemaps/json/town.json");
  }

  create(): void {
    this.scene.start("town-scene");
  }
}

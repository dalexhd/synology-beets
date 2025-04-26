"""Provides a fallback for LastGenre by fetching genres from Spotify when
LastGenre returns 'Unknown'.  Spotify tags are canonicalised through
lastgenre's whitelist/tree.
"""

from beets.plugins import BeetsPlugin
from beets import plugins, ui, library, util
from beets.ui import decargs
from beets.importer import action
from beetsplug.lastgenre import LastGenrePlugin            # NEW
import logging, requests, os, time

class GenreFallbackPlugin(BeetsPlugin):
    """Fetch genres from Spotify when LastGenre leaves 'Unknown'."""

    # ------------------------------------------------------------------ #
    #  INIT                                                               #
    # ------------------------------------------------------------------ #
    def __init__(self):
        super().__init__()

        self.config.add({
            'fallback_for': 'Unknown',
            'separator': ', ',
            'max_genres': 3,
            'retry_delay': 2,
            'max_retries': 3,
            'overwrite': False,
        })

        # locate running lastgenre
        self.lastgenre_plugin = None
        for p in plugins.find_plugins():
            if isinstance(p, LastGenrePlugin):
                self.lastgenre_plugin = p
                break
        if not self.lastgenre_plugin:
            self._log.warning("LastGenre plugin not found; canonical mapping disabled.")

        # import stage
        self.import_stages = [self._stage_fix_unknown]

        # keep CLI-side hook
        self.register_listener('item_imported', self.on_item_imported)

        self.spotify_plugin = None
        self.logger = logging.getLogger('beets.genrefallback')
        self._log.info("GenreFallbackPlugin (early-stage version) initialised")

    # ------------------------------------------------------------------ #
    #  PIPELINE STAGE                                                    #
    # ------------------------------------------------------------------ #
    def _stage_fix_unknown(self, session, task):
        items = task.items if task.is_album else [task.item]
        for it in items:
            if self.check_and_update_genre(item=it):
                if hasattr(it, '_destination'):
                    it._destination = None

    # ------------------------------------------------------------------ #
    #  CLI COMMAND                                                       #
    # ------------------------------------------------------------------ #
    def commands(self):
        cmd = ui.Subcommand('genrefallback', help='update genres from Spotify')
        cmd.parser.add_option('--force', dest='force', action='store_true',
                              help='update even if genre is not Unknown')
        def func(lib, opts, args):
            updated = 0
            for it in lib.items(decargs(args)):
                if opts.force or it.genre == self.config['fallback_for'].get(str):
                    if self.check_and_update_genre(item=it):
                        updated += 1
            self._log.info("Updated {} out of {} items.", updated, len(lib.items(decargs(args))))
        cmd.func = func
        return [cmd]

    # ------------------------------------------------------------------ #
    #  SPOTIFY HELPERS                                                   #
    # ------------------------------------------------------------------ #
    def get_spotify_plugin(self):
        if self.spotify_plugin is None:
            for p in plugins.find_plugins():
                if p.__class__.__name__ == 'SpotifyPlugin':
                    self.spotify_plugin = p
                    break
        if not self.spotify_plugin:
            self._log.error("SpotifyPlugin not found. Make sure it's enabled.")
        return self.spotify_plugin

    def search_track_genre(self, item):
        """Return list of genres from Spotify (artist + album)."""
        spotify = self.get_spotify_plugin()
        if not spotify:
            return None

        query_filters = {"artist": item.artist, "album": item.album}
        try:
            tracks = spotify._search_api(query_type="track",
                                         keywords=item.title,
                                         filters=query_filters)
            if not tracks:
                self._log.debug("No Spotify results for track: {}", item)
                return None

            track = tracks[0] if len(tracks) == 1 else max(
                tracks, key=lambda t: t.get("popularity", 0))

            artist_id = track["artists"][0]["id"]
            artist_genres = spotify._handle_response(
                requests.get, f"https://api.spotify.com/v1/artists/{artist_id}"
            ).get("genres", [])

            album_id = track["album"]["id"]
            album_genres = spotify._handle_response(
                requests.get, f"https://api.spotify.com/v1/albums/{album_id}"
            ).get("genres", [])

            return artist_genres + [g for g in album_genres if g not in artist_genres]
        except Exception as e:
            self._log.error("Error fetching genre from Spotify: {}", e)
            return None

    # --------------------------------------------------------------------- #
    #  Keep the older late-stage logic only for CLI operations               #
    # --------------------------------------------------------------------- #
    def on_item_imported(self, lib, item):
        """Fallback for already-imported items edited later."""
        if item.genre == self.config['fallback_for'].get(str):
            if self.check_and_update_genre(item=item):
                item._destination = None
                item.store()

    # (CLI command, Spotify helpers, and many event hooks remain unchanged)

    # --------------------------------------------------------------------- #
    #  check_and_update_genre – added canonicalisation                       #
    # --------------------------------------------------------------------- #
    def check_and_update_genre(self, lib=None, item=None, **kwargs):
        """Check if a track's genre is Unknown and update from Spotify if needed."""
        if not item:
            return
            
        fallback_for = self.config['fallback_for'].get(str)
        overwrite = self.config['overwrite'].get(bool)
        
        if item.genre == fallback_for or (overwrite and not item.genre):
            self._log.info("Track '{}' has genre '{}', searching Spotify", item.title, item.genre)
            
            # Try to get genres from Spotify
            genres = self.search_track_genre(item)
            
            if genres and len(genres) > 0:
                # ----- Canonicalise through lastgenre whitelist/tree -----
                if self.lastgenre_plugin:
                    genres = self.lastgenre_plugin._resolve_genres(genres)
                    if not genres:
                        self._log.info("Spotify genres rejected by whitelist for '{}'", item.title)
                        return False
                # ---------------------------------------------------------

                # Limit number of genres and join with separator
                max_genres = self.config['max_genres'].get(int)
                separator = self.config['separator'].get(str)
                
                genres = genres[:max_genres]
                new_genre = separator.join(genres)
                
                # Update the genre
                old_genre = item.genre
                item.genre = new_genre
                item.store()
                
                self._log.info("Updated genre for '{}' from '{}' to '{}'", item.title, old_genre, new_genre)
                return True
            else:
                self._log.info("Could not find genres on Spotify for '{}'", item.title)
                
        return False

    def _recalculate_path(self, item, lib):
        """Force recalculation of an item's destination path."""
        try:
            # Path fragment (may be str)
            dest = item.destination(fragment=True)

            # Convert both components to bytes so os.path.join() is happy
            if isinstance(dest, str):
                dest = dest.encode('utf-8')
            lib_dir = util.bytestring_path(lib.directory)

            new_dest = os.path.join(lib_dir, dest)

            # Update DB if needed
            if item.path != new_dest:
                old_path = item.path
                item.path = new_dest
                item.store()
                self._log.info("Updated path from {} to {}", old_path, new_dest)
        except Exception as e:
            self._log.error("Error recalculating path: {}", e)

    def _recalculate_paths(self, items, lib):
        """Force recalculation of destination paths for multiple items."""
        for item in items:
            self._recalculate_path(item, lib)
        """Check if a track's genre is Unknown and update from Spotify if needed."""
        if not item:
            return
            
        fallback_for = self.config['fallback_for'].get(str)
        overwrite = self.config['overwrite'].get(bool)
        
        if item.genre == fallback_for or (overwrite and not item.genre):
            self._log.info("Track '{}' has genre '{}', searching Spotify", item.title, item.genre)
            
            # Try to get genres from Spotify
            genres = self.search_track_genre(item)
            
            if genres and len(genres) > 0:
                # Limit number of genres and join with separator
                max_genres = self.config['max_genres'].get(int)
                separator = self.config['separator'].get(str)
                
                genres = genres[:max_genres]
                new_genre = separator.join(genres)
                
                # Update the genre
                old_genre = item.genre
                item.genre = new_genre
                item.store()
                
                self._log.info("Updated genre for '{}' from '{}' to '{}'", item.title, old_genre, new_genre)
                return True
            else:
                self._log.info("Could not find genres on Spotify for '{}'", item.title)
                
        return False
from __future__ import annotations

import mido


class MidiFile:
    """
    A MidiFile consists of multiple tracks, each track containing multiple notes.
    For our project, we want to keep only one track, the "main one".
    The idea is to parse everything, and then guess which track is the main one.
    """

    def __init__(self, path: str, default_bpm: int = 120):
        # user infos
        self.path = path
        self.default_bpm = default_bpm

        # midi infos
        self.mido_file = mido.MidiFile(path)
        self.ticks_per_beat = self.mido_file.ticks_per_beat
        self.default_midi_tempo = mido.bpm2tempo(default_bpm)
        self.tracks = [Track(self, i) for i in range(len(self.mido_file.tracks))]

        # cache
        self._main_track = None

    @property
    def main_track(self) -> Track:
        """
        Find the main track by assuming it has the highest average note.
        Probably terrible idea.
        """
        if self._main_track is None:
            non_empty_tracks = [t for t in self.tracks if len(t.main_channel_notes) > 0]
            self._main_track = max(non_empty_tracks,
                                   key=lambda t: sum(note.midi_note for note in t.main_channel_notes)
                                                 / len(t.main_channel_notes))
        return self._main_track

    def main_track_to_midi_file(self, output_midi_path: str) -> None:
        """
        Convert main track to a new MidiFile.
        Only useful in order to test the global code.
        """
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        last_message_time = 0
        last_added_note = None
        for note in self.main_track.main_channel_notes:
            midi_note = (note.octave + 1) * 12 + Note.NOTE_NAMES.index(note.name)
            note_tick = mido.second2tick(note.start_time - last_message_time, mid.ticks_per_beat, mido.bpm2tempo(120))
            if last_added_note is not None:
                track.append(mido.Message('note_off', note=last_added_note, time=note_tick))
            track.append(mido.Message('note_on', note=midi_note, velocity=64, time=0))
            last_added_note = midi_note
            last_message_time = note.start_time
        mid.save(output_midi_path)

    def set_start_time(self, start_time: float) -> None:
        """
        Set this time to first note, and add corresponding offset to following notes.
        """
        main_track_offset = start_time - self.main_track.main_channel_notes[0].start_time
        for track in self.tracks:
            track.apply_offset(main_track_offset)

    def to_dict(self) -> dict:
        """
        Return nice dict ready to be jsonified.
        """
        return self.main_track.to_dict()


class Track:
    def __init__(self,
                 parent_file: MidiFile,
                 track_index: int):
        self.parent_file = parent_file
        self.track_index = track_index
        self.mido_track: mido.MidiTrack = parent_file.mido_file.tracks[track_index]
        self._midi_tempo = None
        self._notes_by_channel = None
        self._main_channel_notes = None

    @property
    def notes_by_channel(self) -> dict[str, list[Note]]:
        """
        Property (call without parenthesis) to get notes. Only parse the track once, then it is cached.
        """
        if self._notes_by_channel is None:
            # parse message in track to instanciate notes
            self._notes_by_channel = {}
            current_time = 0
            active_notes_by_channel = {}
            midi_tempo = self.parent_file.default_midi_tempo
            for msg in self.mido_track:
                current_time += mido.tick2second(msg.time, self.parent_file.ticks_per_beat, midi_tempo)
                if msg.type == 'set_tempo':
                    midi_tempo = msg.tempo
                elif msg.type == 'note_on' and msg.velocity > 0:
                    active_notes_by_channel.setdefault(msg.channel, []).append(Note(msg.note, current_time))
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    for note in active_notes_by_channel.get(msg.channel, []):
                        if note.midi_note == msg.note:
                            self._notes_by_channel.setdefault(msg.channel, []).append(note)
                            active_notes_by_channel[msg.channel].remove(note)
                            break
                # if multiple notes are active, keep only the highest one
                for channel, active_notes in active_notes_by_channel.items():
                    if len(active_notes) > 1:
                        active_notes_by_channel[channel] = [max(active_notes, key=lambda n: n.midi_note)]
        return self._notes_by_channel

    @property
    def main_channel_notes(self) -> list[Note]:
        if self._main_channel_notes is None:
            # let's assume best channel is the one with the most diverse notes
            best_channel = max(self.notes_by_channel.keys(),
                               key=lambda c: len(set(n.midi_note for n in self.notes_by_channel[c])))
            self._main_channel_notes = self.notes_by_channel[best_channel]
        return self._main_channel_notes

    def to_dict(self) -> dict:
        """
        Return nice dict.
        """
        return {
            'notes': [note.to_dict() for note in self.main_channel_notes]
        }

    def apply_offset(self, time_offset: float):
        """
        Apply an offset to all notes.
        """
        for channel in self.notes_by_channel.values():
            for note in channel:
                note.start_time += time_offset


class Note:
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def __init__(self, midi_note: int, start_time: float):
        self.midi_note = midi_note
        self.start_time = start_time
        self.name = Note.NOTE_NAMES[midi_note % 12]
        self.octave = midi_note // 12 - 1

    def to_dict(self) -> dict:
        """
        Return nice dict.
        """
        return {
            "start_time": round(self.start_time, 2),
            "name": self.name,
            "octave": self.octave
        }


if __name__ == '__main__':
    import json

    # instantiate MidiFile
    song = MidiFile(r"AxelF.mid", 120)
    song.set_start_time(0)

    # export to json
    d = song.to_dict()
    with open("output.json", "w") as f:
        json.dump(d, f, indent=2)
    print(json.dumps(d['notes'], indent=2)[:1000], "...")

    # export to midi
    song.main_track_to_midi_file(r"output.mid")

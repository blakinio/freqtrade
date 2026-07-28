# ASE-00 E2E after factory alignment

- exit code: `1`

```text
============================= test session starts ==============================
platform linux -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0 -- /home/runner/work/freqtrade/freqtrade/ai_strategy_engine/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/freqtrade/freqtrade
configfile: pyproject.toml
plugins: cov-7.1.0, anyio-4.14.2
collecting ... collected 12 items

tests/ai_platform_integration/test_ase00_vertical_slice.py::test_complete_synthetic_shadow_flow_uses_existing_risk_core FAILED [  8%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_duplicate_event_is_idempotent FAILED [ 16%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_delayed_event_is_accepted_when_available_before_decision FAILED [ 25%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_out_of_order_event_input_is_normalized FAILED [ 33%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_future_feature_is_rejected_fail_closed FAILED [ 41%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_unconfirmed_pivot_is_rejected FAILED [ 50%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_unconfirmed_htf_record_is_rejected PASSED [ 58%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_existing_risk_core_rejection_is_preserved FAILED [ 66%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_restart_and_replay_produces_identical_evidence FAILED [ 75%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_missing_liquidation_data_fails_closed PASSED [ 83%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_conflicting_duplicate_fails_closed_with_reason_code PASSED [ 91%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_adapter_has_no_execution_or_freqtrade_dependency PASSED [100%]

=================================== FAILURES ===================================
_________ test_complete_synthetic_shadow_flow_uses_existing_risk_core __________

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
>           return self._engine.get_loc(casted_key)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3641: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
pandas/_libs/index.pyx:168: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/index.pyx:197: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/hashtable_class_helper.pxi:7668: in pandas._libs.hashtable.PyObjectHashTable.get_item
    ???
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

>   ???
E   KeyError: 'supertrend'

pandas/_libs/hashtable_class_helper.pxi:7676: KeyError

The above exception was the direct cause of the following exception:

    def test_complete_synthetic_shadow_flow_uses_existing_risk_core() -> None:
>       evidence = _engine().run(
            events=_events(),
            strategy_document=_strategy(),
            decision_time=_decision_time(),
            risk_limits=_limits(),
            risk_snapshot=_snapshot(),
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:224: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
ai_platform/research/strategy_engine/ase00_adapter.py:441: in _features
    value = _row_mapping(
ai_platform/research/strategy_engine/ase00_adapter.py:809: in _row_mapping
    return {column: _json_scalar(frame[column].iloc[position]) for column in columns}
                                 ^^^^^^^^^^^^^
ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/frame.py:4378: in __getitem__
    indexer = self.columns.get_loc(key)
              ^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
            return self._engine.get_loc(casted_key)
        except KeyError as err:
            if isinstance(casted_key, slice) or (
                isinstance(casted_key, abc.Iterable)
                and any(isinstance(x, slice) for x in casted_key)
            ):
                raise InvalidIndexError(key) from err
>           raise KeyError(key) from err
E           KeyError: 'supertrend'

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3648: KeyError
______________________ test_duplicate_event_is_idempotent ______________________

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
>           return self._engine.get_loc(casted_key)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3641: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
pandas/_libs/index.pyx:168: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/index.pyx:197: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/hashtable_class_helper.pxi:7668: in pandas._libs.hashtable.PyObjectHashTable.get_item
    ???
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

>   ???
E   KeyError: 'supertrend'

pandas/_libs/hashtable_class_helper.pxi:7676: KeyError

The above exception was the direct cause of the following exception:

    def test_duplicate_event_is_idempotent() -> None:
        events = _events()
>       first = _engine().run(
            events=events,
            strategy_document=_strategy(),
            decision_time=_decision_time(),
            risk_limits=_limits(),
            risk_snapshot=_snapshot(),
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:247: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
ai_platform/research/strategy_engine/ase00_adapter.py:441: in _features
    value = _row_mapping(
ai_platform/research/strategy_engine/ase00_adapter.py:809: in _row_mapping
    return {column: _json_scalar(frame[column].iloc[position]) for column in columns}
                                 ^^^^^^^^^^^^^
ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/frame.py:4378: in __getitem__
    indexer = self.columns.get_loc(key)
              ^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
            return self._engine.get_loc(casted_key)
        except KeyError as err:
            if isinstance(casted_key, slice) or (
                isinstance(casted_key, abc.Iterable)
                and any(isinstance(x, slice) for x in casted_key)
            ):
                raise InvalidIndexError(key) from err
>           raise KeyError(key) from err
E           KeyError: 'supertrend'

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3648: KeyError
________ test_delayed_event_is_accepted_when_available_before_decision _________

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
>           return self._engine.get_loc(casted_key)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3641: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
pandas/_libs/index.pyx:168: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/index.pyx:197: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/hashtable_class_helper.pxi:7668: in pandas._libs.hashtable.PyObjectHashTable.get_item
    ???
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

>   ???
E   KeyError: 'supertrend'

pandas/_libs/hashtable_class_helper.pxi:7676: KeyError

The above exception was the direct cause of the following exception:

    def test_delayed_event_is_accepted_when_available_before_decision() -> None:
        events = _events()
        events[-1] = replace(
            events[-1],
            available_at=events[-1].detected_at + timedelta(seconds=2),
        )
        decision_time = events[-1].available_at + timedelta(seconds=1)
>       evidence = _engine().run(
            events=events,
            strategy_document=_strategy(),
            decision_time=decision_time,
            risk_limits=_limits(),
            risk_snapshot=_snapshot(),
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:273: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
ai_platform/research/strategy_engine/ase00_adapter.py:441: in _features
    value = _row_mapping(
ai_platform/research/strategy_engine/ase00_adapter.py:809: in _row_mapping
    return {column: _json_scalar(frame[column].iloc[position]) for column in columns}
                                 ^^^^^^^^^^^^^
ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/frame.py:4378: in __getitem__
    indexer = self.columns.get_loc(key)
              ^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
            return self._engine.get_loc(casted_key)
        except KeyError as err:
            if isinstance(casted_key, slice) or (
                isinstance(casted_key, abc.Iterable)
                and any(isinstance(x, slice) for x in casted_key)
            ):
                raise InvalidIndexError(key) from err
>           raise KeyError(key) from err
E           KeyError: 'supertrend'

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3648: KeyError
_________________ test_out_of_order_event_input_is_normalized __________________

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
>           return self._engine.get_loc(casted_key)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3641: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
pandas/_libs/index.pyx:168: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/index.pyx:197: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/hashtable_class_helper.pxi:7668: in pandas._libs.hashtable.PyObjectHashTable.get_item
    ???
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

>   ???
E   KeyError: 'supertrend'

pandas/_libs/hashtable_class_helper.pxi:7676: KeyError

The above exception was the direct cause of the following exception:

    def test_out_of_order_event_input_is_normalized() -> None:
>       ordered = _engine().run(
            events=_events(),
            strategy_document=_strategy(),
            decision_time=_decision_time(),
            risk_limits=_limits(),
            risk_snapshot=_snapshot(),
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:285: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
ai_platform/research/strategy_engine/ase00_adapter.py:441: in _features
    value = _row_mapping(
ai_platform/research/strategy_engine/ase00_adapter.py:809: in _row_mapping
    return {column: _json_scalar(frame[column].iloc[position]) for column in columns}
                                 ^^^^^^^^^^^^^
ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/frame.py:4378: in __getitem__
    indexer = self.columns.get_loc(key)
              ^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
            return self._engine.get_loc(casted_key)
        except KeyError as err:
            if isinstance(casted_key, slice) or (
                isinstance(casted_key, abc.Iterable)
                and any(isinstance(x, slice) for x in casted_key)
            ):
                raise InvalidIndexError(key) from err
>           raise KeyError(key) from err
E           KeyError: 'supertrend'

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3648: KeyError
_________________ test_future_feature_is_rejected_fail_closed __________________

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
>           return self._engine.get_loc(casted_key)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3641: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
pandas/_libs/index.pyx:168: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/index.pyx:197: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/hashtable_class_helper.pxi:7668: in pandas._libs.hashtable.PyObjectHashTable.get_item
    ???
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

>   ???
E   KeyError: 'supertrend'

pandas/_libs/hashtable_class_helper.pxi:7676: KeyError

The above exception was the direct cause of the following exception:

    def test_future_feature_is_rejected_fail_closed() -> None:
        events = _events()
        decision_time = _decision_time()
        events[-2] = replace(events[-2], available_at=decision_time + timedelta(seconds=1))
>       evidence = _engine().run(
            events=events,
            strategy_document=_strategy(),
            decision_time=decision_time,
            risk_limits=_limits(),
            risk_snapshot=_snapshot(),
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:308: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
ai_platform/research/strategy_engine/ase00_adapter.py:441: in _features
    value = _row_mapping(
ai_platform/research/strategy_engine/ase00_adapter.py:809: in _row_mapping
    return {column: _json_scalar(frame[column].iloc[position]) for column in columns}
                                 ^^^^^^^^^^^^^
ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/frame.py:4378: in __getitem__
    indexer = self.columns.get_loc(key)
              ^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
            return self._engine.get_loc(casted_key)
        except KeyError as err:
            if isinstance(casted_key, slice) or (
                isinstance(casted_key, abc.Iterable)
                and any(isinstance(x, slice) for x in casted_key)
            ):
                raise InvalidIndexError(key) from err
>           raise KeyError(key) from err
E           KeyError: 'supertrend'

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3648: KeyError
______________________ test_unconfirmed_pivot_is_rejected ______________________

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
>           return self._engine.get_loc(casted_key)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3641: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
pandas/_libs/index.pyx:168: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/index.pyx:197: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/hashtable_class_helper.pxi:7668: in pandas._libs.hashtable.PyObjectHashTable.get_item
    ???
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

>   ???
E   KeyError: 'supertrend'

pandas/_libs/hashtable_class_helper.pxi:7676: KeyError

The above exception was the direct cause of the following exception:

    def test_unconfirmed_pivot_is_rejected() -> None:
        events = _events()
>       baseline = _engine().run(
            events=events,
            strategy_document=_strategy(),
            decision_time=_decision_time(),
            risk_limits=_limits(),
            risk_snapshot=_snapshot(),
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:323: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
ai_platform/research/strategy_engine/ase00_adapter.py:441: in _features
    value = _row_mapping(
ai_platform/research/strategy_engine/ase00_adapter.py:809: in _row_mapping
    return {column: _json_scalar(frame[column].iloc[position]) for column in columns}
                                 ^^^^^^^^^^^^^
ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/frame.py:4378: in __getitem__
    indexer = self.columns.get_loc(key)
              ^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
            return self._engine.get_loc(casted_key)
        except KeyError as err:
            if isinstance(casted_key, slice) or (
                isinstance(casted_key, abc.Iterable)
                and any(isinstance(x, slice) for x in casted_key)
            ):
                raise InvalidIndexError(key) from err
>           raise KeyError(key) from err
E           KeyError: 'supertrend'

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3648: KeyError
________________ test_existing_risk_core_rejection_is_preserved ________________

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
>           return self._engine.get_loc(casted_key)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3641: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
pandas/_libs/index.pyx:168: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/index.pyx:197: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/hashtable_class_helper.pxi:7668: in pandas._libs.hashtable.PyObjectHashTable.get_item
    ???
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

>   ???
E   KeyError: 'supertrend'

pandas/_libs/hashtable_class_helper.pxi:7676: KeyError

The above exception was the direct cause of the following exception:

    def test_existing_risk_core_rejection_is_preserved() -> None:
>       evidence = _engine().run(
            events=_events(),
            strategy_document=_strategy(),
            decision_time=_decision_time(),
            risk_limits=_limits(),
            risk_snapshot=_snapshot(intent_notional="1001"),
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:381: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
ai_platform/research/strategy_engine/ase00_adapter.py:441: in _features
    value = _row_mapping(
ai_platform/research/strategy_engine/ase00_adapter.py:809: in _row_mapping
    return {column: _json_scalar(frame[column].iloc[position]) for column in columns}
                                 ^^^^^^^^^^^^^
ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/frame.py:4378: in __getitem__
    indexer = self.columns.get_loc(key)
              ^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
            return self._engine.get_loc(casted_key)
        except KeyError as err:
            if isinstance(casted_key, slice) or (
                isinstance(casted_key, abc.Iterable)
                and any(isinstance(x, slice) for x in casted_key)
            ):
                raise InvalidIndexError(key) from err
>           raise KeyError(key) from err
E           KeyError: 'supertrend'

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3648: KeyError
_____________ test_restart_and_replay_produces_identical_evidence ______________

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
>           return self._engine.get_loc(casted_key)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3641: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
pandas/_libs/index.pyx:168: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/index.pyx:197: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/hashtable_class_helper.pxi:7668: in pandas._libs.hashtable.PyObjectHashTable.get_item
    ???
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

>   ???
E   KeyError: 'supertrend'

pandas/_libs/hashtable_class_helper.pxi:7676: KeyError

The above exception was the direct cause of the following exception:

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-0/test_restart_and_replay_produc0')

    def test_restart_and_replay_produces_identical_evidence(tmp_path: Path) -> None:
        path = tmp_path / "shadow-evidence.json"
>       first = _engine().run(
            events=_events(),
            strategy_document=_strategy(),
            decision_time=_decision_time(),
            risk_limits=_limits(),
            risk_snapshot=_snapshot(),
            evidence_path=path,
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:396: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
ai_platform/research/strategy_engine/ase00_adapter.py:441: in _features
    value = _row_mapping(
ai_platform/research/strategy_engine/ase00_adapter.py:809: in _row_mapping
    return {column: _json_scalar(frame[column].iloc[position]) for column in columns}
                                 ^^^^^^^^^^^^^
ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/frame.py:4378: in __getitem__
    indexer = self.columns.get_loc(key)
              ^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = Index(['atr', 'supertrend_up', 'supertrend_down', 'supertrend_direction',
       'supertrend_band', 'supertrend_distance_atr', 'supertrend_flip'],
      dtype='str')
key = 'supertrend'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
            return self._engine.get_loc(casted_key)
        except KeyError as err:
            if isinstance(casted_key, slice) or (
                isinstance(casted_key, abc.Iterable)
                and any(isinstance(x, slice) for x in casted_key)
            ):
                raise InvalidIndexError(key) from err
>           raise KeyError(key) from err
E           KeyError: 'supertrend'

ai_strategy_engine/.venv/lib/python3.12/site-packages/pandas/core/indexes/base.py:3648: KeyError
=============================== warnings summary ===============================
ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464
  /home/runner/work/freqtrade/freqtrade/ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464
  /home/runner/work/freqtrade/freqtrade/ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: asyncio_mode
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_complete_synthetic_shadow_flow_uses_existing_risk_core - KeyError: 'supertrend'
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_duplicate_event_is_idempotent - KeyError: 'supertrend'
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_delayed_event_is_accepted_when_available_before_decision - KeyError: 'supertrend'
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_out_of_order_event_input_is_normalized - KeyError: 'supertrend'
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_future_feature_is_rejected_fail_closed - KeyError: 'supertrend'
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_unconfirmed_pivot_is_rejected - KeyError: 'supertrend'
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_existing_risk_core_rejection_is_preserved - KeyError: 'supertrend'
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_restart_and_replay_produces_identical_evidence - KeyError: 'supertrend'
=================== 8 failed, 4 passed, 2 warnings in 3.41s ====================

```

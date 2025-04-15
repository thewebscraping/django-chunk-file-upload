.PHONY: docs
init:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

lint:
	python -m black django_chunk_file_upload
	python -m isort django_chunk_file_upload
	python -m flake8 django_chunk_file_upload


publish-test-pypi:
	python -m pip install -r requirements.txt
	python -m pip install wheel
	python -m pip install 'twine>=6.0.1'
	python setup.py sdist bdist_wheel
	twine upload --repository testpypi dist/*
	rm -rf build dist .egg django_chunk_file_upload.egg-info

publish-pypi:
	python -m pip install -r requirements.txt
	python -m pip install wheel
	python -m pip install 'twine>=6.0.1'
	python setup.py sdist bdist_wheel
	twine upload dist/*
	rm -rf build dist .egg django_chunk_file_upload.egg-info

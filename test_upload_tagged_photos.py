#!/usr/bin/env python
# -*- coding: utf-8 -*-

# builtin
import os
import shutil
import ConfigParser

# external
import slumber
from gi.repository import GExiv2

# local
from upload_tagged_photos import ImageUploader


class TestUploadWiki():

    config = ConfigParser.ConfigParser()
    config.read('test.cfg')
    api_url = config.get('localwiki', 'api_url')
    user_name = config.get('localwiki', 'user_name')
    api_key = config.get('localwiki', 'api_key')
    main_keyword = config.get('localwiki', 'main_keyword')

    test_page_names = ['Existing Upload Test Page',
                       'Non Existing Upload Test Page']

    test_directories = ['test-dir-01', 'test-dir-02']

    test_files = [['photo-with-tags-01.jpg',
                   'photo-with-tags-01.png'],
                  ['photo-with-tags-02.jpg',
                   'photo-with-tags-02.png']]

    def setup(self):

        self.api = slumber.API(self.api_url)

        # create directories with images, some with correct keywords
        for directory, test_page_name in zip(self.test_directories,
                                             self.test_page_names):
            file_names = os.listdir(directory)
            for file_name in file_names:
                if '-with-' in file_name:
                    metadata = GExiv2.Metadata(os.path.join(directory,
                                                            file_name))
                    metadata.set_tag_multiple('Iptc.Application2.Keywords',
                                              [self.main_keyword, 'page:' +
                                               test_page_name])
                    metadata.save_file()

        # create a test page that doesn't have the images on it
        page_dict = {"content": "<p>The Existing Upload Test Page.</p>",
                     "name": self.test_page_names[0],
                     }
        try:
            self.api.page.post(page_dict, username=self.user_name,
                               api_key=self.api_key)
        except slumber.exceptions.HttpServerError:
            self.api.page(page_dict['name']).delete(username=self.user_name,
                                                   api_key=self.api_key)
            self.api.page.post(page_dict, username=self.user_name,
                               api_key=self.api_key)

        test_page_slug = self.api.page(page_dict['name']).get()['slug']

        file_path = os.path.join(self.test_directories[0],
                                 self.test_files[0][0])
        with open(file_path, 'r') as f:
            self.api.file.post({'name': os.path.split(file_path)[1],
                                'slug': test_page_slug}, files={'file': f},
                               username=self.user_name,
                               api_key=self.api_key)

        # TODO : create some images with the Exif such that the images have
        # to be rotated before upload.

        self.uploader = ImageUploader(self.api_url,
                                      user_name=self.user_name,
                                      api_key=self.api_key)

    def test_init(self):

        assert self.uploader.api._store['base_url'] == self.api_url
        assert self.uploader.api._store['format'] == 'json'

    def test_remove_tmp_dirs(self):
        directories = ['localwikidir1', 'localwikidir2']
        for directory in directories:
            os.mkdir(os.path.join('/tmp', directory,
                                  self.uploader._tmp_dir_name))
        files = ['file1.jpg', 'file2.jpg']
        file_paths = []
        for directory, file_name in zip(directories, files):
            file_path = os.path.join('/tmp', directory,
                                     self.uploader._tmp_dir_name, file_name)
            with open(file_path, 'w') as f:
                pass
            file_path.append()
            assert os.exists(file_path)

        self.uploader.remove_tmp_dirs(file_paths)

        for file_path in file_paths:
            assert not os.exists(os.split(file_path)[0])
            assert not os.exists(file_path)

        for directory in directories:
            shutil.rmtree(os.path.join('/tmp', directory))

    def test_find_localwiki_images(self):
        self.uploader.directories = self.test_directories
        wiki_images = self.uploader.find_localwiki_images()

        expected_wiki_images = {}
        for directory, page_name, file_names in zip(self.test_directories,
                                                    self.test_page_names,
                                                    self.test_files):
            file_paths = [os.path.join(directory, file_name) for file_name
                          in file_names]
            expected_wiki_images.update(dict(zip(file_paths, len(file_paths)
                                                 * page_name)))

        assert expected_wiki_images == wiki_images

    def test_find_localwiki_images_in_directory(self):

        for directory, page_name in zip(self.test_directories,
                                        self.test_page_names):
            file_names = [f for f in os.listdir(directory) if '-with-' in f]
            wiki_images = \
                self.uploader.find_localwiki_images_in_directory(
                    self, directory)
            file_paths = [os.path.join(directory, file_name) for file_name
                          in file_names]
            expected_wiki_images = dict(zip(file_paths, len(file_paths) *
                                            page_name))
            assert expected_wiki_images == wiki_images

    def test_create_page(self):
        # create a page that doesn't exist
        page_name = 'This Page Does Not Exist'
        page = self.uploader.create_page(page_name)

        assert page['name'] == page_name
        assert page['content'] == \
            '<p>Please add some content to help describe this page.</p>'

        self.api.page('This Page Does Not Exist').delete(username=self.user_name,
                                                         api_key=self.api_key)

        # create a page that does exist
        page_name = 'Existing Upload Test Page'
        page = self.uploader.create_page(page_name)
        assert page['name'] == page_name
        assert page['content'] == "<p>The Existing Upload Test Page.</p>"

    def test_find_files_in_page(self):

        non_page_name = 'this will never be the name of a page'
        assert self.uploader.find_files_in_page(non_page_name) is None

        files_in_page = \
            self.uploader.find_files_in_page('Existing Upload Test Page')
        assert files_in_page[0]['name'] == 'photo-with-tags.jpg'
        assert files_in_page[0]['slug'] == 'existing upload test page'

    def test_file_exists_on_server(self):

        assert not self.uploader.file_exists_on_server('booglediddly.png')
        assert self.uploader.file_exists_on_server('photo-with-tags.jpg')

    def test_rotate_image(self):
        pass

        # TODO : create rotated images
        #self.uploader.rotate_image(image_file_path)

        #directory, file_name = os.path.split(image_file_path)

        #rotated_file_path = os.path.join(directory, self.uploader._tmp_dir, file_name)
        #assert os.exists(rotated_file_path)

        #metadata = GExiv2.Metadata(rotated_file_path)
        #assert metadata['Exif.Image.Orientation'] == '1'

    def test_embed_image(self):
        page_info = self.uploader.embed_image(self.test_page_names[0],
                                              'photo-with-tags-01.png')
        expected_content = \
"""
<p>
  <span class="image_frame image_frame_border">
    <img src="_files/photo-with-tags-01.png" style="width: 300px; height: 225px;" />
    <span class="image_caption" style="width: 300px;">
      Caption me!
    </span>
  </span>
</p>
"""
        assert expected_content in page_info['content']

        page_info = self.uploader.embed_image(self.test_page_names[0],
                                              'booger.png')
        assert page_info is None

    def test_upload_image(self):
        page_info = self.api.page.get(self.test_page_name[0])
        self.uploader.upload_image(page_info,
                                   os.path.join(self.test_directories[0],
                                                'photo-without-tags.jpg'))
        files = self.api.file.get(slug='existing upload page')['objects']
        assert 'photo-without-tags.jpg' in [f['name'] for f in files]

    def test_upload(self):
        self.uploader.upload(self.main_keyword, *self.test_directories)

        for page_name, test_files in zip(self.test_page_names,
                                         self.test_files):
            page_info = self.api.page.get(page_name)
            files = self.api.file.get(slug=page_info['slug'])
            file_names_on_server = [f['name'] for f in files]
            for file_name in test_files:
                assert file_name in file_names_on_server

    def teardown(self):

        # remove all keywords from the test images
        for directory in self.test_directories:
            file_names = os.listdir(directory)
            for file_name in file_names:
                if '-with-' in file_name:
                    metadata = GExiv2.Metadata(os.path.join(directory,
                                                            file_name))
                    metadata.clear_tag('Iptc.Application2.Keywords')
                    metadata.save_file()

        # remove the files attached to the test page and the test pages from
        # the server
        for page_name in self.test_page_names:
            files = self.api.file.get(slug=page_name.lower())['objects']
            for f in files:
                # TODO : delete or get by file id doesn't seem to work
                self.api.file(f['id']).delete(username=self.user_name,
                                              api_key=self.api_key)
            self.api.page(page_name).delete(username=self.user_name,
                                            api_key=self.api_key)

        # TODO : Move into the test
        # delete the tmp image directories
        directories = ['localwikidir1', 'localwikidir2']
        for directory in directories:
            shutil.rmtree(os.path.join('/tmp', directory,
                                       self.uploader._tmp_dir_name))

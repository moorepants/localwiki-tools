#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard library
import os
import shutil
import ConfigParser

# external libraries
import slumber
from gi.repository import GExiv2

# local libraries
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

    caption = 'The cool caption.'

    def delete_server_side(self):
        """Deletes the files from the test pages and then the pages
        themselves."""

        # the server
        for page_name in self.test_page_names + ['This Page Does Not Exist']:
            try:
                self.api.page(page_name).get()
            except slumber.exceptions.HttpClientError:
                pass
            else:
                files = self.api.file.get(slug=page_name.lower())['objects']
                for f in files:
                    self.api.file(f['id']).delete(username=self.user_name,
                                                  api_key=self.api_key)
                    print("Deleted {} from {} on the server.".format(
                        f['name'], page_name))
                self.api.page(page_name).delete(username=self.user_name,
                                                api_key=self.api_key)
                print("Deleted {} from the server".format(page_name))

    def setup(self):

        self.api = slumber.API(self.api_url, append_slash=False)

        # create directories with images, some with correct keywords
        for directory, test_page_name in zip(self.test_directories,
                                             self.test_page_names):
            file_names = os.listdir(directory)
            for file_name in file_names:
                if True in [file_name.endswith(ext) for ext in
                            ImageUploader._file_extensions]:
                    metadata = GExiv2.Metadata(os.path.join(directory,
                                                            file_name))
                    if '-with-' in file_name:
                        keywords = [self.main_keyword, 'page:' +
                                    test_page_name]
                        metadata.set_tag_multiple('Iptc.Application2.Keywords',
                                                keywords)
                        print('Added keywords {} to {}.'.format(keywords,
                                                                file_name))
                    metadata['Exif.Image.Orientation'] = '1'
                    metadata['Iptc.Application2.Caption'] = self.caption
                    # TODO : add a 'template:<template name>' tag to one of
                    # the files to test if it get's noticed.
                    metadata.save_file()

        # delete any files/pages that may have been leftover from previous
        # tests
        self.delete_server_side()

        # create a test page that doesn't have the images on it
        page_dict = {"content": "<p>The Existing Upload Test Page.</p>",
                     "name": self.test_page_names[0],
                     }

        self.api.page.post(page_dict, username=self.user_name,
                           api_key=self.api_key)
        print('Created {} on the server.'.format(self.test_page_names[0]))

        test_page_slug = self.api.page(page_dict['name']).get()['slug']

        file_path = os.path.join(self.test_directories[0],
                                 self.test_files[0][0])
        with open(file_path, 'r') as f:
            self.api.file.post({'name': os.path.split(file_path)[1],
                                'slug': test_page_slug}, files={'file': f},
                               username=self.user_name,
                               api_key=self.api_key)
        print('Added {} to {}.'.format(file_path, self.test_page_names[0]))

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
            os.mkdir(os.path.join('/tmp', directory))
            os.mkdir(os.path.join('/tmp', directory,
                                  self.uploader._tmp_dir_name))
        files = ['file1.jpg', 'file2.jpg']
        file_paths = []
        for directory, file_name in zip(directories, files):
            file_path = os.path.join('/tmp', directory,
                                     self.uploader._tmp_dir_name, file_name)
            with open(file_path, 'w') as f:
                pass
            file_paths.append(file_path)
            assert os.path.exists(file_path)

        self.uploader.remove_tmp_dirs([os.path.join('/tmp', d, f) for d, f
                                       in zip(directories, files)])

        for file_path in file_paths:
            assert not os.path.isdir(os.path.split(file_path)[0])
            assert not os.path.exists(file_path)

        for directory in directories:
            shutil.rmtree(os.path.join('/tmp', directory))

    def test_find_localwiki_images(self):
        self.uploader.directories = self.test_directories
        self.uploader.main_keyword = self.main_keyword
        wiki_images = self.uploader.find_localwiki_images()

        expected_wiki_images = {}
        for directory, page_name, file_names in zip(self.test_directories,
                                                    self.test_page_names,
                                                    self.test_files):
            file_paths = [os.path.join(directory, file_name) for file_name
                          in file_names]
            expected_wiki_images.update(dict(zip(file_paths, zip(len(file_paths)
                                                 * [[page_name]], len(file_paths)
                                                                 * [None]))))

        assert expected_wiki_images == wiki_images

    def test_find_localwiki_images_in_directory(self):

        for directory, page_name in zip(self.test_directories,
                                        self.test_page_names):
            file_names = [f for f in os.listdir(directory) if '-with-' in f]
            self.uploader.main_keyword = self.main_keyword
            wiki_images = \
                self.uploader.find_localwiki_images_in_directory(directory)
            file_paths = [os.path.join(directory, file_name) for file_name
                          in file_names]
            expected_wiki_images = dict(zip(file_paths, zip(len(file_paths) *
                                            [[page_name]], len(file_paths) * [None])))
            assert expected_wiki_images == wiki_images

    def test_create_page(self):
        # create a page that doesn't exist
        page_name = 'This Page Does Not Exist'
        self.uploader.create_page(page_name)
        page = self.api.page(page_name).get()
        assert page['name'] == page_name
        assert page['content'] == self.uploader._stub_page_content

        self.api.page('This Page Does Not Exist').delete(
            username=self.user_name, api_key=self.api_key)

        # create a page that does exist
        page_name = 'Existing Upload Test Page'
        page = self.uploader.create_page(page_name)
        assert page['name'] == page_name
        assert page['content'] == "<p>The Existing Upload Test Page.</p>"

        # test page creation with a template
        page_name = 'This Page Does Not Exist And Has A Template'
        self.uploader.create_page(page_name, template_name='Business')
        page = self.api.page(page_name).get()
        template = self.api.page('Templates/Business').get()
        assert template['content'] in page['content']
        self.api.page(page_name).delete(
            username=self.user_name, api_key=self.api_key)

    def test_find_files_in_page(self):

        non_page_name = 'this will never be the name of a page'
        assert self.uploader.find_files_in_page(non_page_name) is None

        files_in_page = \
            self.uploader.find_files_in_page('Existing Upload Test Page')
        assert files_in_page[0]['name'] == 'photo-with-tags-01.jpg'
        assert files_in_page[0]['slug'] == 'existing upload test page'

    def test_file_exists_on_server(self):

        assert not self.uploader.file_exists_on_server('booglediddly.png')
        assert self.uploader.file_exists_on_server('photo-with-tags-01.jpg')

    def test_rotate_image(self):

        tmp_image_path = 'tmp_rotation_test_image.jpg'
        shutil.copyfile('rotation_test_image.jpg', tmp_image_path)

        metadata_before = GExiv2.Metadata(tmp_image_path)

        self.uploader.rotate_image(tmp_image_path)

        metadata_after = GExiv2.Metadata(tmp_image_path)

        assert metadata_after['Exif.Image.Orientation'] == '1'
        assert metadata_after.get_pixel_height() == \
            metadata_before.get_pixel_width()
        assert metadata_after.get_pixel_width() == \
            metadata_before.get_pixel_height()

        os.remove('tmp_rotation_test_image.jpg')

    def test_embed_image(self):
        page_info = self.uploader.embed_image(self.test_page_names[0],
                                              'photo-with-tags-01.jpg',
                                              3.0 / 4.0, caption=self.caption)
        expected_content = \
"""
<p>
  <span class="image_frame image_frame_border">
    <img src="_files/photo-with-tags-01.jpg" style="width: 300px; height: 400px;" />
    <span class="image_caption" style="width: 300px;">
      {}
    </span>
  </span>
</p>
""".format(self.caption)

        assert expected_content in page_info['content']

        page_info = self.uploader.embed_image(self.test_page_names[0],
                                              'booger.png', 1.0)
        assert page_info is None

    def test_upload_image(self):
        page_info = self.api.page(self.test_page_names[0]).get()
        self.uploader.upload_image(page_info,
                                   os.path.join(self.test_directories[0],
                                                'photo-without-tags-01.jpg'))
        files = self.api.file.get(slug=page_info['slug'])['objects']
        assert 'photo-without-tags-01.jpg' in [f['name'] for f in files]

    def test_upload(self):
        self.uploader.upload(self.main_keyword, *self.test_directories)

        for page_name, test_files in zip(self.test_page_names,
                                         self.test_files):
            page_info = self.api.page(page_name).get()
            files = self.api.file.get(slug=page_info['slug'])['objects']
            file_names_on_server = [f['name'] for f in files]
            for file_name in test_files:
                assert file_name in file_names_on_server

    def test_resize_image_to_1024(self):
        image_path = 'resize_test_image.jpg'
        tmp_image_path = 'tmp_resize_test_image.jpg'
        shutil.copyfile(image_path, tmp_image_path)

        metadata_before = GExiv2.Metadata(tmp_image_path)
        aspect_ratio = (float(metadata_before.get_pixel_width()) /
                        float(metadata_before.get_pixel_height()))

        self.uploader.resize_image_to_1024(image_path, tmp_image_path)

        metadata_after = GExiv2.Metadata(tmp_image_path)

        assert metadata_after.get_pixel_width() == 1024
        assert metadata_after.get_pixel_height() == int(1024 / aspect_ratio)

        for tag in metadata_before.get_exif_tags() + metadata_before.get_iptc_tags():
            assert metadata_after[tag] == metadata_before[tag]

        # TODO : assert that image doesn't change if it is less than 1024

        os.remove(tmp_image_path)

    def teardown(self):

        # remove all keywords from the test images
        for directory in self.test_directories:
            file_names = os.listdir(directory)
            for file_name in file_names:
                if True in [file_name.endswith(ext) for ext in
                            ImageUploader._file_extensions]:
                    metadata = GExiv2.Metadata(os.path.join(directory,
                                                            file_name))
                    metadata.clear_tag('Iptc.Application2.Keywords')
                    metadata.clear_tag('Iptc.Application2.Caption')
                    metadata.save_file()
                    print('Cleared tags from {}.'.format(file_name))

        # remove the files attached to the test page and the test pages from
        # the server
        self.delete_server_side()

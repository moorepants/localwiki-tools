#!/usr/bin/env python
# -*- coding: utf-8 -*-

from upload_tagged_photos import ImageUploader

def TestUploadWiki():

    url = "http://clevelandwiki.org/api/"
    user_name = raw_input("What is your username?")
    api_key = getpassword("What is your api_key?")

    def setup(self):

        self.api = slumber.API(self.url, auth=(self.user_name,
                                               self.password))

        # create two directories with some images, some should have correct
        # tags

        # create test page
        page_dict = {
                "content": "<p>The Upload Test Page.</p>",
                "name": "Upload Test Page",
        }
        test_page = self.api.page.post(page_dict)
        test_page_slug = self.api.page(test_page['id'])['slug']

        # add an image to it
        with open('image.jpg') as f:
            self.api.file.post(name='image.jpg', slug=test_page_slug,
                            files={'file': f})

        self.uploader = ImageUploader(self.api_url,
                                      user_name=self.user_name,
                                      api_key=self.api_key)

    def test_init(self):

        assert self.uploader.api._store['base_url'] == self.api_url
        assert self.uploader.api._store['format'] == 'json'
        assert self.uploader.api._store['session'].auth[0] == self.user_name
        assert self.uploader.api._store['session'].auth[1] == self.api_key

    def test_remove_tmp_dirs():
        directories = ['localwikidir1', 'localwikidir2']
        for directory in directories:
            os.mkdir(os.path.join('/tmp', directory,
                                  self.uploader._tmp_dir_name))
        files = ['file1.jpg', 'file2.jpg']
        file_paths = []
        for directory, file_name in zip(directores, files):
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
        pass

    def test_find_localwiki_images_in_directory(self):

        wiki_images = \
            self.uploader.find_localwiki_images_in_directory(
                self, '/tmp/localwiki')

        expected_wiki_images = {'/tmp/localwiki/image.jpg':
                                ['Upload Test Page']}

        assert wiki_images == expected_wiki_images

    def test_create_page(self):
        # create a page that doesn't exist
        page_name = 'This Page Does Not Exist'
        page = self.uploader.create_page(page_name)

        assert page['name'] == page_name
        assert page['content'] == \
            '<p>Please add some content to help describe this page.</p>'

        self.api.page('This Page Does Not Exist').delete()

        # create a page that does exist
        page_name = 'Upload Test Page'
        page = self.uploader.create_page(page_name)
        assert page['name'] == page_name
        assert page['content'] == "<p>The Upload Test Page.</p>"

    def test_find_files_in_page(self):

        assert find_files_in_page('this will never be the name of a page') is None
        files_in_page = find_files_in_page('Upload Test Page')
        assert files_in_page[0]['name'] = 'image.jpg'
        assert files_in_page[0]['slug'] = 'upload test page'

    def test_file_exists_on_server(self):

        assert not self.uploader.file_exists_on_server('booglediddly.png')
        assert self.uploader.file_exists_on_server('image.jpg')

    def test_rotate_image(self):

        self.uploader.rotate_image(image_file_path)

        directory, file_name = os.path.split(image_file_path)

        rotated_file_path = os.path.join(directory, self.uploader._tmp_dir, file_name)
        assert os.exists(rotated_file_path)

        metadata = GExiv2.Metadata(rotated_file_path)
        assert metadata['Exif.Image.Orientation'] == '1'

    def teardown():
        # remove the files attached to the test page
        # delete the test page and all versions
        # delete the tmp image directories
        test_page = api.page('Upload Test Page').get()
        test_file_id = \
            api.files.get(slug=test_page['slug'])['objects'][0]['id']
        self.api.files.id.delete()
        self.api.page('Upload Test Page').delete()



def test_find_wiki_images():
    os.mkdir('/tmp/wiki-images')

upload_wiki_images('dir'])
upload_wiki_images(['dir1', 'dir2'])
upload_wiki_images('dir'], create_new_page=True, embed_image_on_create=True)

wiki_images = find_wiki_images('dir')
wiki_images = find_wiki_images(['dir1', 'dir2'])

wiki_images['/tmp/cw/test_image.jpg'] == ['page:Test Page']

check_if_file_exists(file_name)
